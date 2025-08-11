# tests/models/test_listings_models.py
import pytest
from listings.models import Amenity, Listing

@pytest.mark.django_db
def test_listing_amenities_and_history(landlord_user):
    wifi, _ = Amenity.objects.get_or_create(name="WiFi")
    park, _ = Amenity.objects.get_or_create(name="Parking")

    listing = Listing.objects.create(
        user=landlord_user,
        title="Test",
        description="Desc",
        price_per_night=100,
        address="Berlin Street 1",
        rooms=2,
        property_type="Apartment",
        is_active=True
    )
    listing.amenities.add(wifi, park)
    names = [a.name for a in listing.amenities.all()]
    assert "WiFi" in names and "Parking" in names
    assert listing.history.exists()
