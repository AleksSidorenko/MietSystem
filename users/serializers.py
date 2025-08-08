# users/serializers.py
import re
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        # Добавляем user_id в полезную нагрузку токена
        refresh["user_id"] = (
            self.user.id
        )  # <- Это правильно для добавления user_id в токен обновления
        return data

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(use_url=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    # Убираем read_only=True. Теперь мы будем контролировать это в get_serializer_class.
    role = serializers.CharField()
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "role_display",
            "language",
            "avatar",
            "is_active",
            "is_verified",
            "date_joined",
            "password",
        ]
        read_only_fields = ('is_verified', 'is_active', 'date_joined')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_phone_number(self, value):
        if value and not re.match(r"^\+?[1-9]\d{1,14}$", value):
            raise serializers.ValidationError(_("Invalid phone number format"))
        return value

    def validate_email(self, value):
        if self.instance is None and User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("Email already exists"))
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

class TOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = TOTPDevice
        fields = ["id", "name", "confirmed"]

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]
