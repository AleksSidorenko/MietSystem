# bookings/tests/test_serializers.py
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from bookings.serializers import BookingSerializer
from listings.models import AvailabilitySlot

class MockRequest:
    def __init__(self, user, method="POST"):
        self.user = user
        self.method = method


@pytest.mark.django_db
class TestBookingSerializer:
    def test_valid_booking_data(self, listing, tenant_user):
        listing.is_active = True
        listing.price_per_night = Decimal('100.00')
        listing.save()

        # Используем get_or_create, чтобы избежать ошибок дублирования
        for i in range(1, 4):
            AvailabilitySlot.objects.get_or_create(
                listing=listing,
                date=date.today() + timedelta(days=i),
                defaults={"is_available": True}
            )

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        serializer = BookingSerializer(data=data, context={"request": MockRequest(user=tenant_user, method="POST")})

        # Проверяем валидность
        serializer.is_valid(raise_exception=True)

        # Сохраняем и получаем объект booking
        booking = serializer.save()

        # Проверяем total_price на объекте, а не в validated_data
        assert booking.total_price == 2 * listing.price_per_night

    def test_cannot_book_inactive_listing(self, listing, tenant_user):
        listing.is_active = False
        listing.save()
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=2)).isoformat(),
        }
        serializer = BookingSerializer(data=data, context={"request": MockRequest(user=tenant_user, method="POST")})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_selected_dates_not_available(self, listing, tenant_user):
        # Создаем слоты с get_or_create, чтобы не дублировать
        AvailabilitySlot.objects.get_or_create(listing=listing, date=date.today()+timedelta(days=1), defaults={"is_available": True})
        AvailabilitySlot.objects.get_or_create(listing=listing, date=date.today()+timedelta(days=2), defaults={"is_available": False})
        AvailabilitySlot.objects.get_or_create(listing=listing, date=date.today()+timedelta(days=3), defaults={"is_available": True})

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        serializer = BookingSerializer(data=data, context={"request": MockRequest(user=tenant_user, method="POST")})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_end_date_before_start_date(self, listing, tenant_user):
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=5)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        serializer = BookingSerializer(data=data, context={"request": MockRequest(user=tenant_user, method="POST")})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_duration_too_long(self, listing, tenant_user):
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=40)).isoformat(),
        }
        serializer = BookingSerializer(data=data, context={"request": MockRequest(user=tenant_user, method="POST")})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_selected_dates_not_available(self, listing, tenant_user):
        # Создаем слоты с get_or_create, чтобы не дублировать
        AvailabilitySlot.objects.update_or_create(
            listing=listing,
            date=date.today() + timedelta(days=1),
            defaults={"is_available": True}
        )
        AvailabilitySlot.objects.update_or_create(
            listing=listing,
            date=date.today() + timedelta(days=2),
            defaults={"is_available": False}
        )
        AvailabilitySlot.objects.update_or_create(
            listing=listing,
            date=date.today() + timedelta(days=3),
            defaults={"is_available": True}
        )
        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        serializer = BookingSerializer(data=data, context={"request": MockRequest(user=tenant_user, method="POST")})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
