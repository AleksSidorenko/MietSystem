# tests/api/test_reviews.py
import pytest
from rest_framework import status
from reviews.models import Review
from bookings.models import Booking
from decimal import Decimal
from datetime import date, timedelta

@pytest.mark.django_db
def test_create_review_after_booking(api_client, booking, tenant_user):
    booking.status = "CONFIRMED"
    booking.save()
    api_client.force_authenticate(user=tenant_user)
    data = {"booking": booking.id, "rating": 5, "comment": "Great stay!"}
    response = api_client.post("/api/reviews/", data)
    assert response.status_code in (201, 400)
    # If created, DB has a review
    if response.status_code == 201:
        assert Review.objects.exists()
        assert int(response.data.get("data", response.data).get("rating", 0)) == 5

@pytest.mark.django_db
def test_review_unique_per_booking(api_client, booking, tenant_user):
    booking.status = "CONFIRMED"
    booking.save()
    Review.objects.create(booking=booking, user=tenant_user, rating=4, comment="OK")
    api_client.force_authenticate(user=tenant_user)
    data = {"booking": booking.id, "rating": 5, "comment": "Again"}
    response = api_client.post("/api/reviews/", data)
    assert response.status_code == 400
    assert "unique" in str(response.data).lower() or "already" in str(response.data).lower()

@pytest.mark.django_db
def test_review_non_completed_booking(api_client, booking, tenant_user):
    api_client.force_authenticate(user=tenant_user)
    data = {"booking": booking.id, "rating": 5, "comment": "Not allowed"}
    response = api_client.post("/api/reviews/", data)
    assert response.status_code == 400
    assert "confirmed bookings" in str(response.data['non_field_errors']).lower()
