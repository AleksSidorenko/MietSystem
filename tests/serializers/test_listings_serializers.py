# tests/serializers/test_listings_serializers.py
import pytest
from rest_framework.exceptions import ValidationError
from listings.serializers import ListingSerializer
from datetime import date, timedelta


@pytest.mark.django_db
def test_listing_serializer_valid(landlord_user, sample_amenities):
    # sample_amenities содержит Amenity объекты, включая "WiFi"
    data = {
        "title": "Test Apartment",
        "description": "Nice place",
        "price_per_night": 100,
        "address": "Berlin",
        "rooms": 2,
        "property_type": "Apartment",
        "amenities": [a.name for a in sample_amenities],  # или [a.id for a in sample_amenities] в зависимости от сериализатора
        "availability": [
            {"date": (date.today() + timedelta(days=1)).isoformat(), "is_available": True}
        ],
    }
    serializer = ListingSerializer(
        data=data, context={"request": type("Request", (), {"user": landlord_user})}
    )
    assert serializer.is_valid(), f"errors: {serializer.errors}"


@pytest.mark.django_db
def test_listing_serializer_invalid_price():
    data = {"title": "Test", "price_per_night": -10, "address": "Berlin", "rooms": 1}
    serializer = ListingSerializer(data=data)
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)
