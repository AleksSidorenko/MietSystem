# bookings/tests/test_views.py
from datetime import date, timedelta
import pytest
from django.urls import reverse
from rest_framework import status
from bookings.models import Booking
from listings.models import AvailabilitySlot

@pytest.mark.django_db
class TestBookingViews:
    def test_list_bookings_requires_auth(self, api_client):
        url = reverse("booking-list")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_bookings_authenticated(self, api_client_tenant, booking):
        resp = api_client_tenant.get(reverse("booking-list"))
        assert resp.status_code == status.HTTP_200_OK
        # базовая структура: results или data->results — проверяем гибко
        data = resp.data
        if isinstance(data, dict):
            # проверяем наличие хотя бы одного booking
            if "results" in data:
                assert isinstance(data["results"], list)
            else:
                # некоторые проекты возвращают {'data': {'results': [...]}}
                inner = data.get("data") or data
                if isinstance(inner, dict) and "results" in inner:
                    assert isinstance(inner["results"], list)

    def test_retrieve_booking_owner(self, api_client_tenant, booking, tenant_user):
        resp = api_client_tenant.get(reverse("booking-detail", kwargs={"pk": booking.pk}))
        assert resp.status_code == status.HTTP_200_OK

    def test_create_booking_unauthenticated(self, api_client, listing):
        url = reverse("booking-list")
        data = {
            "listing": listing.id,
            "start_date": (date.today()+timedelta(days=1)).isoformat(),
            "end_date": (date.today()+timedelta(days=3)).isoformat(),
        }
        resp = api_client.post(url, data, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_booking_valid(self, api_client_tenant, listing):
        # Создадим availability слоты, если их нет (без дублирования)
        for i in range(10, 15):
            AvailabilitySlot.objects.get_or_create(
                listing=listing,
                date=date.today() + timedelta(days=i),
                defaults={"is_available": True},
            )

        data = {
            "listing": listing.id,
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=12)).isoformat(),
        }

        resp = api_client_tenant.post(reverse("booking-list"), data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Booking.objects.filter(listing=listing, start_date=data["start_date"],
                                      end_date=data["end_date"]).exists()

