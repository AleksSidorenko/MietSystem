# listings/serializers.py
import io
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from PIL import Image
from rest_framework import serializers
from locations.serializers import LocationSerializer
from utils.translation import TranslationSerializerMixin
from listings.models import Listing, ListingPhoto, Amenity


class AvailabilitySlotSerializer(serializers.Serializer):
    date = serializers.DateField()
    is_available = serializers.BooleanField()

class ListingSerializer(TranslationSerializerMixin, serializers.ModelSerializer):
    amenities = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Amenity.objects.all(),
        required=False,
    )
    # amenities = serializers.ListField(child=serializers.CharField(), required=False)
    url = serializers.HyperlinkedIdentityField(view_name='listing-detail')  # <-- НОВОЕ ПОЛЕ
    availability = serializers.SerializerMethodField()
    location = LocationSerializer(read_only=True)
    main_photo = serializers.SerializerMethodField()

    @extend_schema_field(
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "format": "date"},
                    "is_available": {"type": "boolean"},
                },
                "required": ["date", "is_available"],
            },
        }
    )
    def get_availability(self, obj):
        """
        Возвращает список словарей, представляющих доступность объекта.
        Каждый словарь содержит 'date' (строка в формате ISO) и 'is_available' (булево).
        """
        return [
            {"date": slot.date.isoformat(), "is_available": slot.is_available}
            for slot in obj.availability_slots.all()
        ]

    # --- НОВЫЙ МЕТОД ДЛЯ ПОЛУЧЕНИЯ ГЛАВНОГО ФОТО ---
    @extend_schema_field(str)
    def get_main_photo(self, obj):
        """
        Возвращает URL главной фотографии (первой по порядку).
        """
        # Используем related_name 'gallery' из модели ListingPhoto
        first_photo = obj.gallery.order_by('order').first()

        if first_photo and first_photo.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(first_photo.image.url)
            return first_photo.image.url
        return None

    class Meta:
        model = Listing
        fields = [
            "url",  # <-- ДОБАВЛЕНО ПОЛЕ
            "id",
            "user",
            "title",
            "description",
            "address",
            "price_per_night",
            "rooms",
            "property_type",
            "amenities",
            "main_photo",
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

    # def validate_amenities(self, value):
    #     if not isinstance(value, list):
    #         raise serializers.ValidationError(_("Amenities must be a list"))
    #     amenities_objs = []
    #     for name in value:
    #         amenity, _ = Amenity.objects.get_or_create(name=name)
    #         amenities_objs.append(amenity)
    #     return amenities_objs

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
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Availability must be a list of dictionaries")
            )
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    _("Each availability item must be a dictionary")
                )
            date_str = item.get("date")
            is_available = item.get("is_available")

            if not isinstance(date_str, str) or not isinstance(is_available, bool):
                raise serializers.ValidationError(
                    _(
                        "Each availability item must be a dictionary with 'date' (string) and 'is_available' (boolean)"
                    )
                )

        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not hasattr(request, "user") or request.user.is_anonymous:
            raise serializers.ValidationError(_("User must be authenticated to create a listing"))

        amenities = validated_data.pop("amenities", [])
        validated_data.pop("user", None)  # <-- Убираем user, если он есть

        listing = Listing.objects.create(user=request.user, **validated_data)
        if amenities:
            listing.amenities.set(amenities)
        return listing

    def update(self, instance, validated_data):
        amenities = validated_data.pop("amenities", None)
        instance = super().update(instance, validated_data)
        if amenities is not None:
            instance.amenities.set(amenities)
        return instance


class ListingShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["id", "title", "price_per_night", "city", "country"]
