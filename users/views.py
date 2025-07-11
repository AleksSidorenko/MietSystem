### `users/views.py`

from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, VerificationToken
from .permissions import IsAdmin, IsAuthenticated
from .serializers import TOTPSerializer, UserSerializer
from .tasks import send_reset_password_email, send_verification_email


class CustomTokenObtainPairView(TokenObtainPairView):
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
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email.delay(user.id)

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
    @csrf_protect
    def totp(self, request):
        if request.method == "GET":
            devices = TOTPDevice.objects.filter(user=request.user)
            serializer = TOTPSerializer(devices, many=True)
            return Response(serializer.data)
        elif request.method == "POST":
            device = TOTPDevice.objects.create(user=request.user, name="default")
            serializer = TOTPSerializer(device)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django_otp.plugins.otp_totp.models import TOTPDevice
# from .models import User
# from .serializers import UserSerializer, TOTPSerializer
# from .permissions import IsAdmin, IsAuthenticated
# from .tasks import send_verification_email, send_reset_password_email
#
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsAdmin]
#
#     def perform_create(self, serializer):
#         user = serializer.save()
#         send_verification_email.delay(user.id)
#
#     @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
#     def email_verification(self, request):
#         user = request.user
#         if user.is_verified:
#             return Response({"error": "Email already verified"}, status=status.HTTP_400_BAD_REQUEST)
#         user.is_verified = True
#         user.save()
#         return Response({"message": "Email verified"}, status=status.HTTP_200_OK)
#
#     @action(detail=False, methods=['post'], permission_classes=[])
#     def password_reset(self, request):
#         email = request.data.get('email')
#         try:
#             user = User.objects.get(email=email)
#             send_reset_password_email.delay(user.id)
#             return Response({"message": "Password reset email sent"}, status=status.HTTP_200_OK)
#         except User.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#
#     @action(detail=False, methods=['get', 'post'], permission_classes=[IsAuthenticated])
#     def totp(self, request):
#         if request.method == 'GET':
#             devices = TOTPDevice.objects.filter(user=request.user)
#             serializer = TOTPSerializer(devices, many=True)
#             return Response(serializer.data)
#         elif request.method == 'POST':
#             device = TOTPDevice.objects.create(user=request.user, name='default')
#             serializer = TOTPSerializer(device)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
