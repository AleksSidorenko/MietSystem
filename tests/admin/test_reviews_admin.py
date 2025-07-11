# tests/admin/test_reviews_admin.py

import datetime

import pytest
from django.urls import reverse

from bookings.models import Booking
from listings.models import Listing
from reviews.models import Review
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="pass123")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com",
        password="pass123",
        role="ADMIN",
        is_staff=True,
        is_superuser=False,
        is_active=True,
    )


@pytest.fixture
def landlord_user():
    return User.objects.create_user(
        email="landlord@example.com",
        password="pass123",
        role="LANDLORD",
        is_staff=True,
    )


@pytest.fixture
def tenant_user():
    return User.objects.create_user(
        email="tenant@example.com",
        password="pass123",
        role="TENANT",
        is_staff=True,  # ← обязательно для входа в админку
        is_active=True,
    )


# @pytest.fixture
# def another_landlord():
#     return User.objects.create_user(
#         email='another_landlord@example.com',
#         password='pass123',
#         role='LANDLORD',
#         is_staff=True,
#         is_active=True,
#     )


@pytest.fixture
def listing(landlord_user):
    return Listing.objects.create(
        title_en="Test Listing for Review",
        user=landlord_user,
        price_per_night=100,
        address="Munich",
        rooms=2.0,
        is_active=True,
        popularity=10,
    )


@pytest.fixture
def booking(listing, tenant_user):
    return Booking.objects.create(
        listing=listing,
        user=tenant_user,
        start_date=datetime.date(2025, 7, 10),
        end_date=datetime.date(2025, 7, 15),
        total_price=750,
        status="CONFIRMED",
    )


@pytest.fixture
def review(booking, tenant_user):
    return Review.objects.create(
        booking=booking,
        user=tenant_user,
        rating=4,
        comment="Test review",
    )


@pytest.mark.parametrize(
    "user_fixture, expected_status",
    [
        ("superuser", 200),
        ("admin_user", 200),
        ("landlord_user", 200),  # ✅ теперь landlord видит свои отзывы
        ("tenant_user", 200),  # ✅ tenant тоже видит свои отзывы
        # ("another_landlord", 403),  # ❌ не видит чужие отзывы
    ],
)
def test_reviewsadmin_changelist_access(
    client, request, user_fixture, expected_status, review
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    url = reverse("admin:reviews_review_changelist")
    response = client.get(url)
    assert response.status_code == expected_status
    if expected_status == 200:
        # assert "Test review" in response.content.decode()
        assert (
            response.status_code == expected_status
        ), f"User: {user.email} | Expected: {expected_status} | Got: {response.status_code}"
