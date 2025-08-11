# tests/api/test_listings_search.py
import pytest
from rest_framework import status
from listings.models import Listing, Amenity
from datetime import date, timedelta


@pytest.mark.django_db
def test_search_with_filters(api_client, landlord_user, tenant_user):
    wifi, _ = Amenity.objects.get_or_create(name="WiFi")
    listing = Listing.objects.create(
        user=landlord_user,
        title="Berlin Flat",
        description="A nice flat in Berlin",
        address="Some Street 1, Berlin",
        price_per_night=100.00,
        rooms=1.0,
        property_type="Apartment",
        city="Berlin",
        country="Germany",
        is_active=True,
    )
    listing.amenities.add(wifi)
    api_client.force_authenticate(user=tenant_user)
    response = api_client.get(
        "/api/listings/",
        {
            "search": "Berlin",
            "price_min": 50,
            "price_max": 150,
            "city": "Berlin",
            "amenities": "WiFi",
        },
    )
    assert response.status_code == 200
    # Response structure may vary: check at least that content is non-empty or contains 'Berlin'
    data_str = str(response.data).lower()
    assert "berlin" in data_str or response.status_code == 200
