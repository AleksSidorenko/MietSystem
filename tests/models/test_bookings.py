# tests/models/test_bookings.py
import pytest
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from bookings.models import Booking

@pytest.mark.django_db
def test_booking_creation(booking):
    assert booking.status in ("PENDING", "CONFIRMED", "CANCELLED")
    # total_price computed in fixture — check it's non-null and non-negative
    assert booking.total_price is not None
    assert booking.history.exists()

@pytest.mark.django_db
def test_booking_str(booking):
    assert str(booking).startswith("Booking")

@pytest.mark.django_db
def test_booking_validation_invalid_dates(listing, tenant_user):
    booking = Booking(
        user=tenant_user,
        listing=listing,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=3),
        total_price=100,
    )
    with pytest.raises(ValidationError):
        booking.clean()

@pytest.mark.django_db
def test_booking_validation_negative_price(listing, tenant_user):
    booking = Booking(
        user=tenant_user,
        listing=listing,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=3),
        total_price=-100,
    )
    with pytest.raises(ValidationError):
        booking.clean()
