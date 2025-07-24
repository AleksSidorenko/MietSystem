# locations/serializers.py

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from utils.translation import TranslationSerializerMixin
from .models import Location


class LocationSerializer(TranslationSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "listing",
            # "latitude",
            # "longitude",
            "federal_state",
            "city",
            "postal_code",
            "street",
        ]

    def validate_postal_code(self, value):
        if value and not value.isdigit() or len(value) != 5:
            raise serializers.ValidationError(_("Postal code must be a 5-digit number"))
        return value

    def validate_latitude(self, value):
        if value is not None and not -90 <= value <= 90:
            raise serializers.ValidationError(_("Latitude must be between -90 and 90"))
        return value

    def validate_longitude(self, value):
        if value is not None and not -180 <= value <= 180:
            raise serializers.ValidationError(
                _("Longitude must be between -180 and 180")
            )
        return value
