# tests/admin/test_booking_admin.py

from datetime import date, timedelta

import pytest
from django.urls import reverse

from bookings.models import Booking
from listings.models import Listing
from users.models import User

pytestmark = pytest.mark.django_db

# --- Users ---


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="pass")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com", password="pass", role="ADMIN", is_staff=True
    )


@pytest.fixture
def landlord_user():
    return User.objects.create_user(
        email="landlord@example.com", password="pass", role="LANDLORD", is_staff=True
    )


@pytest.fixture
def another_landlord():
    return User.objects.create_user(
        email="another@landlord.com", password="pass", role="LANDLORD", is_staff=True
    )


@pytest.fixture
def tenant_user():
    return User.objects.create_user(
        email="tenant@example.com", password="pass", role="TENANT"
    )


@pytest.fixture
def another_tenant():
    return User.objects.create_user(
        email="tenant2@example.com", password="pass", role="TENANT"
    )


# --- Listings and Bookings ---


@pytest.fixture
def landlord_listing(landlord_user):
    return Listing.objects.create(
        user=landlord_user,
        title="Landlord Listing",
        price_per_night=120,
        address="Berlin",
        rooms=2,
        is_active=True,
    )


@pytest.fixture
def another_listing(another_landlord):
    return Listing.objects.create(
        user=another_landlord,
        title="Other Listing",
        price_per_night=80,
        address="Hamburg",
        rooms=1,
        is_active=True,
    )


@pytest.fixture
def landlord_booking(landlord_listing, tenant_user):
    return Booking.objects.create(
        listing=landlord_listing,
        user=tenant_user,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=3),
        total_price=360,
        status="CONFIRMED",
    )


@pytest.fixture
def unrelated_booking(another_listing, tenant_user):
    return Booking.objects.create(
        listing=another_listing,
        user=tenant_user,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2),
        total_price=160,
        status="CONFIRMED",
    )


# --- Access to Booking list ---


@pytest.mark.parametrize(
    "user_fixture, expected_status",
    [
        ("superuser", 200),
        ("admin_user", 200),
        ("landlord_user", 200),
        ("tenant_user", 302),
    ],
)
def test_bookingadmin_changelist_access(
    client, request, user_fixture, expected_status, landlord_booking
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)
    url = reverse("admin:bookings_booking_changelist")
    response = client.get(url)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert "Landlord Listing" in response.content.decode()


# --- Change permission for allowed users ---


@pytest.mark.parametrize("user_fixture", ["superuser", "admin_user", "landlord_user"])
def test_bookingadmin_change_permission_allowed(
    client, request, user_fixture, landlord_booking
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)
    url = reverse("admin:bookings_booking_change", args=[landlord_booking.pk])
    response = client.get(url)
    assert response.status_code == 200


# --- Change permission forbidden for unrelated users ---


@pytest.mark.parametrize(
    "user_fixture", ["landlord_user", "tenant_user", "another_tenant"]
)
def test_bookingadmin_change_permission_denied(
    client, request, user_fixture, unrelated_booking
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)
    url = reverse("admin:bookings_booking_change", args=[unrelated_booking.pk])
    response = client.get(url)
    assert response.status_code in (302, 403)
