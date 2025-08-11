# tests/conftest.py
from datetime import date, timedelta
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# Import models to ensure apps are populated
from bookings.models import Booking
from listings.models import Listing, Amenity, AvailabilitySlot
from reviews.models import Review
from django.utils import timezone




User = get_user_model()

@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client

@pytest.fixture
def landlord_user(db):
    return User.objects.create_user(
        email="landlord@example.com",
        password="password",
        first_name="John",
        last_name="Doe",
        phone_number="+1234567890",
        role="LANDLORD",
        language="en",
        is_active=True,
        is_verified=True,
        date_joined=timezone.now(),
    )


@pytest.fixture
def tenant_user(db):
    return User.objects.create_user(
        email="tenant@example.com",
        password="testpassword",
        first_name="Jane",
        last_name="Smith",
        role="TENANT",
        is_verified=True,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com",
        password="testpassword",
        first_name="Admin",
        last_name="User",
        role="ADMIN",
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        email="super@example.com",
        password="testpass",
        first_name="Super",
        last_name="User",
    )


@pytest.fixture
def sample_amenities(db):
    names = ["WiFi", "Kitchen", "Air Conditioning", "Parking"]
    out = []
    for n in names:
        a, _ = Amenity.objects.get_or_create(name=n)
        out.append(a)
    return out


@pytest.fixture
def sample_listing_data(sample_amenities):
    return {
        "title": "Cozy Apartment in City Center",
        "description": "A beautifully furnished apartment.",
        "price_per_night": 120.00,
        "address": "123 Main St",
        "city": "Metropolis",
        "country": "Countryland",
        "rooms": 2.5,
        "property_type": "Apartment",
        "is_active": True,
        "popularity": 0,
    }

@pytest.fixture
def listing(db, landlord_user):
    listing = Listing.objects.create(
        user=landlord_user,
        title="Cozy Apartment",
        title_en="Cozy Apartment",
        description="A nice place",
        address="Some Street 1, Berlin",
        city="Berlin",
        country="Germany",
        price_per_night=100.00,
        rooms=2.0,
        property_type="Apartment",
        is_active=True,
        created_at=timezone.now(),
        popularity=0,
    )
    # Add amenities
    wifi, _ = Amenity.objects.get_or_create(name="WiFi")
    listing.amenities.add(wifi)
    # Add availability for day+1 (to cover basic booking)
    for i in range(10, 15):
        AvailabilitySlot.objects.get_or_create(
            listing=listing,
            date=date.today() + timedelta(days=i),
            defaults={"is_available": True}
        )

    return listing

@pytest.fixture
def booking(db, listing, tenant_user):
    start = date.today() + timedelta(days=10)
    end = date.today() + timedelta(days=15)
    duration = (end - start).days
    total_price = duration * listing.price_per_night

    for i in range(duration):
        AvailabilitySlot.objects.get_or_create(
            listing=listing,
            date=start + timedelta(days=i),
            defaults={"is_available": True}
        )

    return Booking.objects.create(
        listing=listing,
        user=tenant_user,
        start_date=start,
        end_date=end,
        total_price=total_price,
        status="PENDING",
    )


@pytest.fixture
def completed_booking(db, booking):
    booking.status = "COMPLETED"
    booking.save()
    return booking


@pytest.fixture
def review(db, completed_booking, tenant_user):
    if completed_booking.status != "COMPLETED":
        completed_booking.status = "COMPLETED"
        completed_booking.save()
    return Review.objects.create(
        booking=completed_booking,
        user=tenant_user,
        rating=4,
        comment="Nice place to stay!",
    )

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def api_client_tenant(tenant_user):
    client = APIClient()
    client.force_authenticate(user=tenant_user)
    return client

@pytest.fixture
def api_client_landlord(landlord_user):
    client = APIClient()
    client.force_authenticate(user=landlord_user)
    return client


@pytest.fixture
def api_client_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def api_client_superuser(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client

@pytest.fixture
def amenities(db):
    from listings.models import Amenity
    amenity_wifi = Amenity.objects.create(name="WiFi")
    # можно добавить еще, если нужно
    return [amenity_wifi]
