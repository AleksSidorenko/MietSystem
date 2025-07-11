### `users/serializers.py`

import re

from django.utils.translation import gettext_lazy as _
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

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

    def validate_role(self, value):
        if value not in [choice[0] for choice in User.ROLE_CHOICES]:
            raise serializers.ValidationError(_("Invalid role"))
        return value

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


# from rest_framework import serializers
# from django_otp.plugins.otp_totp.models import TOTPDevice
# from .models import User
#
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'is_active', 'is_verified']
#         read_only_fields = ['is_active', 'is_verified']
#
#     def validate_role(self, value):
#         if value not in [choice[0] for choice in User.ROLE_CHOICES]:
#             raise serializers.ValidationError("Invalid role")
#         return value
#
# class TOTPSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TOTPDevice
#         fields = ['id', 'name', 'confirmed']
