# locations/serializers.py

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from utils.translation import TranslationSerializerMixin

from .models import Location


class LocationSerializer(TranslationSerializerMixin, serializers.ModelSerializer):
    # Добавляем latitude и longitude как SerlializerMethodField,
    # чтобы они отображались в JSON-ответе, извлекая значения из PointField 'coordinates'.
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id",
            "listing",
            "federal_state",
            "city",
            "postal_code",
            "street",
            "latitude",  # Добавляем сюда SerlializerMethodField
            "longitude",  # Добавляем сюда SerlializerMethodField
            # 'coordinates', # Можете добавить и само поле coordinates, если API-клиенту оно нужно в формате PointField (например, {"type": "Point", "coordinates": [X, Y]})
        ]
        # Если вы хотите, чтобы поле coordinates также отображалось в выводе,
        # убедитесь, что оно не является read_only в Meta, если вы хотите его также и записывать
        # (хотя для Location, оно будет заполняться через LeafletGeoAdmin, а не напрямую через сериализатор API)

    # Метод для получения широты из поля 'coordinates'
    def get_latitude(self, obj):
        return obj.coordinates.y if obj.coordinates else None

    # Метод для получения долготы из поля 'coordinates'
    def get_longitude(self, obj):
        return obj.coordinates.x if obj.coordinates else None

    def validate_postal_code(self, value):
        if value and (not value.isdigit() or len(value) != 5):
            raise serializers.ValidationError(_("Postal code must be a 5-digit number"))
        return value


# from django.utils.translation import gettext_lazy as _
# from rest_framework import serializers
# from utils.translation import TranslationSerializerMixin
# from .models import Location
#
#
# class LocationSerializer(TranslationSerializerMixin, serializers.ModelSerializer):
#     class Meta:
#         model = Location
#         fields = [
#             "id",
#             "listing",
#             # "latitude",
#             # "longitude",
#             "federal_state",
#             "city",
#             "postal_code",
#             "street",
#         ]
#
#     def validate_postal_code(self, value):
#         if value and not value.isdigit() or len(value) != 5:
#             raise serializers.ValidationError(_("Postal code must be a 5-digit number"))
#         return value
