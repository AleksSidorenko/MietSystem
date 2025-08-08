# users/views.py
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from bookings.permissions import IsOwnerOrAdmin
from users.models import User, VerificationToken
from users.permissions import (
    IsAdmin,
    IsAdminUser,
    IsAuthenticated,
    IsSelfOrAdmin,
    IsTenant,
)
from users.serializers import (
    CustomTokenObtainPairSerializer,
    TOTPSerializer,
    UserSerializer,
)
from users.tasks import send_reset_password_email, send_verification_email
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework import generics
from django_ratelimit.core import is_ratelimited

from django.utils.translation import gettext as _
from rest_framework import serializers
from bookings.models import Booking
from listings.models import Listing




User = get_user_model()

class AllUsersForAdminDashboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        role = self.request.query_params.get("role", None)
        queryset = User.objects.all()
        if role:
            queryset = queryset.filter(role=role.upper())
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"users": serializer.data})

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = (
        CustomTokenObtainPairSerializer  # Используем кастомный сериализатор
    )

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

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)

        # Если это ListSerializer, то работаем с его child
        target_serializer = serializer.child if isinstance(serializer, serializers.ListSerializer) else serializer

        # Ограничиваем поле role, если не админ
        if not self.request.user.is_authenticated or self.request.user.role != "ADMIN":
            if 'role' in target_serializer.fields:
                target_serializer.fields['role'].read_only = True

        return serializer

    def get_permissions(self):
        if not hasattr(self, "request") or self.request is None:
            return [IsAuthenticated()]

        # Публичные методы без авторизации
        if self.action in ["password_reset", "password_reset_confirm", "email_verification"]:
            return [AllowAny()]

        # Создание только для админа
        elif self.action == "create":
            return [IsAuthenticated(), IsAdmin()]

        # Остальные требуют авторизации
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsSelfOrAdmin()]

        # Остальное по умолчанию
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()

        if user.role == "ADMIN":
            return User.objects.all().order_by('date_joined')

        elif user.role == "LANDLORD":
            # Арендаторы, которые бронировали объявления лендлорда (listing.user == user)
            tenant_ids = Booking.objects.filter(
                listing__user=user
            ).values_list("user_id", flat=True).distinct()

            return User.objects.filter(
                id__in=tenant_ids
            ).order_by('date_joined')

        elif user.role == "TENANT":
            # Лендлорды, у которых этот тенант бронировал объявления
            landlord_ids = Booking.objects.filter(
                user=user
            ).values_list("listing__user_id", flat=True).distinct()

            return User.objects.filter(
                id__in=landlord_ids
            ).order_by('date_joined')

        return User.objects.none()

    @action(
        detail=False,
        methods=["get", "patch"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == "PATCH":
            if user.role == "ADMIN":
                data_to_update = request.data
            else:
                allowed_fields = ["first_name", "last_name", "email", "phone_number"]
                data_to_update = {
                    field: request.data[field]
                    for field in allowed_fields
                    if field in request.data
                }
            serializer = self.get_serializer(user, data=data_to_update, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def email_verification(self, request):
        # Rate limiting без декораторов
        was_limited = is_ratelimited(
            request=request,
            group='email-verification',
            key='ip',
            rate='100/m',
            method='POST',
            increment=True
        )
        if was_limited:
            return Response({"error": "Too many requests"}, status=429)

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

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def password_reset(self, request):
        was_limited = is_ratelimited(
            request=request, group='password-reset', key='ip', rate='100/m', method='POST', increment=True
        )
        if was_limited:
            return Response({"error": "Too many requests"}, status=429)

        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            send_reset_password_email.delay(user.id)
            return Response({"message": _("Password reset email sent")}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": _("User not found")}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def password_reset_confirm(self, request):
        was_limited = is_ratelimited(
            request=request, group='password-reset-confirm', key='ip', rate='100/m', method='POST', increment=True
        )
        if was_limited:
            return Response({"error": "Too many requests"}, status=429)

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
            return Response({"message": _("Password reset successful")}, status=status.HTTP_200_OK)
        except VerificationToken.DoesNotExist:
            return Response({"error": _("Invalid or expired token")}, status=status.HTTP_400_BAD_REQUEST)

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
