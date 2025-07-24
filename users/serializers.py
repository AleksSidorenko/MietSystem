### ✅ users/serializers.py

# import re
# from rest_framework import serializers
# from django_otp.plugins.otp_totp.models import TOTPDevice
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from users.models import User
# from rest_framework_simplejwt.tokens import RefreshToken
#
#
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         refresh = self.get_token(self.user)
#         data['refresh'] = str(refresh)
#         data['access'] = str(refresh.access_token)
#         refresh['user_id'] = self.user.id
#         return data
#
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = [
#             "id", "email", "first_name", "last_name", "phone",
#             "role", "is_active", "date_joined",
#         ]
#         read_only_fields = ["id", "email", "role", "is_active", "date_joined"]
#
# # class UserSerializer(serializers.ModelSerializer):
# #     password = serializers.CharField(write_only=True, required=False)
# #     role = serializers.CharField(read_only=True)
# #
# #     class Meta:
# #         model = User
# #         fields = [
# #             "id", "email", "first_name", "last_name", "phone_number",
# #             "role", "language", "is_active", "is_verified", "password"
# #         ]
# #         read_only_fields = ["is_active", "is_verified"]
#
#     def validate_phone_number(self, value):
#         if value and not re.match(r"^\+?[1-9]\d{1,14}$", value):
#             raise serializers.ValidationError("Invalid phone number format")
#         return value
#
#     def validate_email(self, value):
#         if self.instance is None and User.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Email already exists")
#         return value
#
#     def create(self, validated_data):
#         password = validated_data.pop("password", None)
#         instance = super().create(validated_data)
#         if password:
#             instance.set_password(password)
#             instance.save()
#         return instance
#
#     def update(self, instance, validated_data):
#         password = validated_data.pop("password", None)
#         instance = super().update(instance, validated_data)
#         if password:
#             instance.set_password(password)
#             instance.save()
#         return instance
#
# class UserUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'phone_number']
#
# class TOTPSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TOTPDevice
#         fields = ["id", "name", "confirmed"]
#
#
# class UserShortSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "email", "first_name", "last_name", "role"]


# users/serializers.py
#
# import re
# from rest_framework import serializers
# from django_otp.plugins.otp_totp.models import TOTPDevice
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from users.models import User
# from rest_framework_simplejwt.tokens import RefreshToken
#
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         refresh = self.get_token(self.user)
#         data['refresh'] = str(refresh)
#         data['access'] = str(refresh.access_token)
#         refresh['user_id'] = self.user.id
#         return data
#
# # from rest_framework import serializers
# # from users.models import User
# #
# #
# # class UserSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = User
# #         fields = [
# #             'id', 'email', 'first_name', 'last_name', 'phone',
# #             'role', 'is_active', 'date_joined',
# #         ]
# #         read_only_fields = ['id', 'email', 'role', 'is_active', 'date_joined']
#
# class UserSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=False)
#     role = serializers.CharField(read_only=True)
#
#     class Meta:
#         model = User
#         fields = [
#             "id", "email", "first_name", "last_name", "phone_number",
#             "role", "language", "is_active", "is_verified", "password"
#         ]
#         read_only_fields = ["is_active", "is_verified"]
#
#     def validate_phone_number(self, value):
#         if value and not re.match(r"^\+?[1-9]\d{1,14}$", value):
#             raise serializers.ValidationError("Invalid phone number format")
#         return value
#
#     def validate_email(self, value):
#         if self.instance is None and User.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Email already exists")
#         return value
#
#     def create(self, validated_data):
#         password = validated_data.pop("password", None)
#         instance = super().create(validated_data)
#         if password:
#             instance.set_password(password)
#             instance.save()
#         return instance
#
#     def update(self, instance, validated_data):
#         password = validated_data.pop("password", None)
#         instance = super().update(instance, validated_data)
#         if password:
#             instance.set_password(password)
#             instance.save()
#         return instance
#
# class UserUpdateSerializer(serializers.ModelSerializer):
#     """Сериализатор для редактирования своего профиля"""
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'phone']
#
# class TOTPSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TOTPDevice
#         fields = ["id", "name", "confirmed"]
#
# class UserShortSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "email", "first_name", "last_name", "role"]


# users/serializers.py

import re
from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        # Добавляем user_id в полезную нагрузку токена
        refresh['user_id'] = self.user.id
        return data

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.CharField(read_only=True)  # Роль только для чтения

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "language",
            "is_active",
            "is_verified",
            "password",
        ]
        read_only_fields = ["is_active", "is_verified"]

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


# class UserSerializer(serializers.ModelSerializer):
#     role = serializers.CharField(read_only=True)
#     # или:
#     # role = serializers.ChoiceField(choices=User.ROLE_CHOICES, read_only=True)
#     password = serializers.CharField(write_only=True, required=False)
#
#     class Meta:
#         model = User
#         fields = [
#             "id",
#             "email",
#             "first_name",
#             "last_name",
#             "phone_number",
#             "role",
#             "language",
#             "is_active",
#             "is_verified",
#             "password",
#         ]
#         read_only_fields = ["is_active", "is_verified"]
#
#     def validate_role(self, value):
#         if value not in [choice[0] for choice in User.ROLE_CHOICES]:
#             raise serializers.ValidationError(_("Invalid role"))
#         return value
#
#     def validate_phone_number(self, value):
#         if value and not re.match(r"^\+?[1-9]\d{1,14}$", value):
#             raise serializers.ValidationError(_("Invalid phone number format"))
#         return value
#
#     def validate_email(self, value):
#         if self.instance is None and User.objects.filter(email=value).exists():
#             raise serializers.ValidationError(_("Email already exists"))
#         return value
#
#     def create(self, validated_data):
#         password = validated_data.pop("password", None)
#         instance = super().create(validated_data)
#         if password:
#             instance.set_password(password)
#             instance.save()
#         return instance
#
#     def update(self, instance, validated_data):
#         request_user = self.context.get('request').user
#
#         if request_user != instance and request_user.role != 'ADMIN':
#             raise serializers.ValidationError("Вы можете редактировать только свои данные.")
#
#         password = validated_data.pop("password", None)
#         instance = super().update(instance, validated_data)
#         if password:
#             instance.set_password(password)
#             instance.save()
#         return instance
#
#     # def update(self, instance, validated_data):
#     #     password = validated_data.pop("password", None)
#     #     instance = super().update(instance, validated_data)
#     #     if password:
#     #         instance.set_password(password)
#     #         instance.save()
#     #     return instance
#
#
class TOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = TOTPDevice
        fields = ["id", "name", "confirmed"]


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]
