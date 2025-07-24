# users/views.py

from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from bookings.permissions import IsOwnerOrAdmin
from users.models import User, VerificationToken
from users.permissions import IsAdmin, IsAuthenticated, IsTenant
from users.tasks import send_reset_password_email, send_verification_email

from users.serializers import CustomTokenObtainPairSerializer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer, TOTPSerializer
from users.permissions import IsAdminUser, IsSelfOrAdmin


User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer  # Используем кастомный сериализатор

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        response.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=3600,  # 1 hour
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=7 * 24 * 3600,  # 7 days
        )
        return response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if not hasattr(self, 'request') or self.request is None:
            return [IsAuthenticated()]  # ← позволяет drf-spectacular сгенерировать схему без авторизации

        if self.action == 'create':
            return [IsAuthenticated(), IsTenant()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]

        return [IsAuthenticated()]

    # def get_permissions(self):
    #     if self.action in ["list", "retrieve", "update", "partial_update", "destroy"]:
    #         return [IsAdminUser()]
    #     elif self.action in ["me"]:
    #         return [IsAuthenticated()]
    #     elif self.action == "create":
    #         return [AllowAny()]
    #     return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == "ADMIN":
            return User.objects.all()
        return User.objects.none()  # Только админ видит других

    @action(detail=False, methods=["get", "patch"], url_path="me", permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == "PATCH":
            allowed_fields = ['first_name', 'last_name', 'email', 'phone_number']
            data = {field: request.data[field] for field in allowed_fields if field in request.data}

            serializer = self.get_serializer(user, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=["post"], permission_classes=[])
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def email_verification(self, request):
        token = request.data.get("token")
        try:
            verification_token = VerificationToken.objects.get(
                token=token, expires_at__gt=timezone.now()
            )
            user = verification_token.user
            if user.is_verified:
                return Response(
                    {"error": _("Email already verified")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.is_verified = True
            user.save()
            verification_token.delete()
            return Response({"message": _("Email verified")}, status=status.HTTP_200_OK)
        except VerificationToken.DoesNotExist:
            return Response(
                {"error": _("Invalid or expired token")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"], permission_classes=[])
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def password_reset(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            send_reset_password_email.delay(user.id)
            return Response(
                {"message": _("Password reset email sent")}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": _("User not found")}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"], permission_classes=[])
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def password_reset_confirm(self, request):
        token = request.data.get("token")
        password = request.data.get("password")
        try:
            verification_token = VerificationToken.objects.get(
                token=token, expires_at__gt=timezone.now()
            )
            user = verification_token.user
            user.set_password(password)
            user.save()
            verification_token.delete()
            return Response(
                {"message": _("Password reset successful")}, status=status.HTTP_200_OK
            )
        except VerificationToken.DoesNotExist:
            return Response(
                {"error": _("Invalid or expired token")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get", "post"], permission_classes=[IsAuthenticated])
    # @csrf_protect
    def totp(self, request):
        if request.method == "GET":
            devices = TOTPDevice.objects.filter(user=request.user)
            serializer = TOTPSerializer(devices, many=True)
            return Response(serializer.data)
        elif request.method == "POST":
            device = TOTPDevice.objects.create(user=request.user, name="default")
            serializer = TOTPSerializer(device)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
