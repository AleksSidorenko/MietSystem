# tests/serializers/test_reviews.py
import pytest
from rest_framework.exceptions import ValidationError
from reviews.serializers import ReviewSerializer
from datetime import date, timedelta
from rest_framework.test import APIRequestFactory
from rest_framework import serializers

from django.utils import timezone

@pytest.mark.django_db
def test_review_serializer_valid(booking, tenant_user):
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()

    # Обновляем бронирование: даты должны быть в прошлом, чтобы отзыв мог быть создан
    booking.start_date = today - timedelta(days=5)
    booking.end_date = today - timedelta(days=1)
    booking.status = "CONFIRMED"  # статус подтвержденного бронирования
    booking.save()

    data = {
        "booking": booking.id,
        "rating": 5,
        "comment": "Excellent stay!"
    }

    factory = APIRequestFactory()
    request = factory.post('/api/reviews/', data)
    request.user = tenant_user

    serializer = ReviewSerializer(data=data, context={"request": request})

    assert serializer.is_valid(), f"errors: {serializer.errors}"

    review = serializer.save()

    assert review.user == tenant_user
    assert review.booking == booking



@pytest.mark.django_db
def test_review_serializer_non_completed_booking(booking, tenant_user):
    data = {"booking": booking.id, "rating": 5, "comment": "Not allowed"}
    factory = APIRequestFactory()
    request = factory.post('/api/reviews/', data)
    request.user = tenant_user
    serializer = ReviewSerializer(data=data, context={"request": request})
    with pytest.raises(serializers.ValidationError, match="confirmed bookings"):
        serializer.is_valid(raise_exception=True)

@pytest.mark.django_db
def test_review_serializer_invalid_rating(booking, tenant_user):
    booking.status = "COMPLETED"
    booking.save()
    data = {"booking": booking.id, "rating": 6, "comment": "Invalid"}
    serializer = ReviewSerializer(data=data)
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)



