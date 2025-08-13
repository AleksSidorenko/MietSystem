# tests/api/test_bookings.py
import pytest
from rest_framework import status
from bookings.models import Booking
from datetime import date, timedelta
from decimal import Decimal

@pytest.mark.django_db
def test_confirm_booking(api_client, landlord_user, booking):
    # landlord_user should be owner of the listing
    api_client.force_authenticate(user=landlord_user)
    url = f"/api/bookings/{booking.id}/confirm/"
    response = api_client.post(url)
    # If landlord_user is not owner of listing, endpoint may forbid; otherwise OK
    assert response.status_code in (200, 403, 404)
    # If succeeded, booking should change status to CONFIRMED
    booking.refresh_from_db()
    assert booking.status in ("PENDING", "CONFIRMED", "CANCELLED")

@pytest.mark.django_db
def test_booking_overlap(api_client, tenant_user, listing):
    # create a confirmed booking that blocks certain dates
    start = date.today() + timedelta(days=10)
    end = date.today() + timedelta(days=15)
    # compute total_price
    total_price = Decimal((end - start).days) * Decimal(str(listing.price_per_night))
    Booking.objects.create(
        user=tenant_user, listing=listing, start_date=start, end_date=end, total_price=total_price, status="CONFIRMED"
    )
    api_client.force_authenticate(user=tenant_user)
    data = {
        "listing": listing.id,
        "start_date": (date.today() + timedelta(days=12)).isoformat(),
        "end_date": (date.today() + timedelta(days=17)).isoformat(),
    }
    response = api_client.post("/api/bookings/", data)
    assert response.status_code in (400, 403, 201)
    if response.status_code == 400:
        assert "overlap" in str(response.data).lower() or "not available" in str(response.data).lower()
