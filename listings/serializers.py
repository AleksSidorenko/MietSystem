### `listings/serializers.py`

import io

from django.utils.translation import gettext_lazy as _
from PIL import Image
from rest_framework import serializers

from locations.serializers import LocationSerializer
from utils.translation import TranslationSerializerMixin

from .models import Listing


class ListingSerializer(TranslationSerializerMixin, serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "user",
            "title",
            "description",
            "address",
            "price_per_night",
            "rooms",
            "property_type",
            "amenities",
            "photos",
            "availability",
            "is_active",
            "created_at",
            "popularity",
            "location",
        ]
        read_only_fields = ["id", "user", "created_at", "popularity", "location"]

    def validate_photos(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(_("Photos must be a list"))
        for photo in value:
            file = photo.get("file")
            if file:
                if file.size > 5 * 1024 * 1024:
                    raise serializers.ValidationError(_("Photo size must be ≤ 5MB"))
                if file.content_type not in ["image/jpeg", "image/png"]:
                    raise serializers.ValidationError(_("Photo must be JPEG or PNG"))
                img = Image.open(io.BytesIO(file.read()))
                if img.width < 200 or img.height < 200:
                    raise serializers.ValidationError(
                        _("Photo dimensions must be ≥ 200px")
                    )
                file.seek(0)
        return value

    def validate_amenities(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(_("Amenities must be a list"))
        return value

    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Price per night must be positive"))
        return value

    def validate_rooms(self, value):
        if value <= 0 or value % 0.5 != 0:
            raise serializers.ValidationError(
                _("Rooms must be a positive integer or half-integer (e.g., 1, 1.5, 2)")
            )
        return value

    def validate_availability(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Availability must be a dictionary"))
        for date, available in value.items():
            if not isinstance(date, str) or not isinstance(available, bool):
                raise serializers.ValidationError(
                    _(
                        "Availability must be a dictionary of date strings to boolean values"
                    )
                )
        return value


class ListingShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["id", "title", "price_per_night", "city", "country"]
