# tests/serializers/test_bookings.py
import pytest
from rest_framework.exceptions import ValidationError
from bookings.serializers import BookingSerializer
from datetime import date, timedelta
from listings.models import AvailabilitySlot
from decimal import Decimal

class MockRequest:
    def __init__(self, user=None, method="POST"):
        self.user = user
        self.method = method

@pytest.mark.django_db
def test_booking_serializer_valid(listing, tenant_user):
    listing.is_active = True
    listing.save()

    # Ensure availability slots exist (use get_or_create)
    for i in range(1, 5):
        AvailabilitySlot.objects.get_or_create(
            listing=listing,
            date=date.today() + timedelta(days=i),
            defaults={"is_available": True},
        )

    data = {
        "listing": listing.id,
        "start_date": (date.today() + timedelta(days=1)).isoformat(),
        "end_date": (date.today() + timedelta(days=3)).isoformat(),
    }
    serializer = BookingSerializer(
        data=data, context={"request": MockRequest(user=tenant_user, method="POST")}
    )
    assert serializer.is_valid(), f"Errors: {serializer.errors}"
    # total_price is readonly and computed in model/save path; validated data should be available
    # create instance to check total_price (serializer.create will call model.save eventually)
    booking = serializer.save()
    expected_total = Decimal((date.today() + timedelta(days=3) - (date.today() + timedelta(days=1))).days) * Decimal(str(listing.price_per_night))
    assert booking.total_price == expected_total

@pytest.mark.django_db
def test_booking_serializer_invalid_dates(listing, tenant_user):
    data = {
        "listing": listing.id,
        "start_date": (date.today() + timedelta(days=5)).isoformat(),
        "end_date": (date.today() + timedelta(days=3)).isoformat(),
    }
    serializer = BookingSerializer(
        data=data, context={"request": MockRequest(user=tenant_user, method="POST")}
    )
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)

@pytest.mark.django_db
def test_booking_serializer_inactive_listing(listing, tenant_user):
    listing.is_active = False
    listing.save()
    # ensure at least one availability slot exists
    AvailabilitySlot.objects.get_or_create(
        listing=listing,
        date=date.today() + timedelta(days=1),
        defaults={"is_available": True},
    )
    data = {
        "listing": listing.id,
        "start_date": (date.today() + timedelta(days=1)).isoformat(),
        "end_date": (date.today() + timedelta(days=3)).isoformat(),
    }
    serializer = BookingSerializer(
        data=data, context={"request": MockRequest(user=tenant_user, method="POST")}
    )
    with pytest.raises(ValidationError, match='Cannot book an inactive listing'):
        serializer.is_valid(raise_exception=True)


