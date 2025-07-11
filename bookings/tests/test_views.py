# bookings/tests/test_views.py

from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from bookings.models import Booking
from listings.models import Listing
from users.models import User


@pytest.fixture
def another_tenant_user():
    return User.objects.create_user(
        email="another_tenant@example.com", password="password", role="TENANT"
    )


@pytest.fixture
def another_landlord_user():
    return User.objects.create_user(
        email="another_landlord@example.com", password="password", role="LANDLORD"
    )


@pytest.fixture
def tenant_user():
    return User.objects.create_user(
        email="tenant@example.com", password="password", role="TENANT"
    )


@pytest.fixture
def owner_user():
    return User.objects.create_user(
        email="owner@example.com", password="password", role="LANDLORD"
    )


@pytest.fixture
def listing(owner_user):
    return Listing.objects.create(
        title="Cozy Apartment in City Center",
        description="A lovely place to stay.",
        user=owner_user,
        price_per_night=100.00,
        address="123 Main St",
        city="Berlin",
        country="Germany",
        latitude=52.5200,
        longitude=13.4050,
        rooms=2.0,
        property_type="Apartment",
        availability={
            (date.today() + timedelta(days=1)).isoformat(): True,
            (date.today() + timedelta(days=2)).isoformat(): True,
            (date.today() + timedelta(days=3)).isoformat(): True,
            (date.today() + timedelta(days=4)).isoformat(): True,
            (date.today() + timedelta(days=5)).isoformat(): True,
            (date.today() + timedelta(days=6)).isoformat(): True,
            (date.today() + timedelta(days=7)).isoformat(): True,
            (date.today() + timedelta(days=8)).isoformat(): True,
            (date.today() + timedelta(days=9)).isoformat(): True,
            (date.today() + timedelta(days=10)).isoformat(): True,
            (date.today() + timedelta(days=11)).isoformat(): True,
            (date.today() + timedelta(days=12)).isoformat(): True,
        },
        is_active=True,
    )


@pytest.fixture
def booking(listing, tenant_user):
    return Booking.objects.create(
        listing=listing,
        user=tenant_user,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=3),
        total_price=200.00,  # Убедитесь, что это значение соответствует price_per_night * количество_дней
        status="CONFIRMED",
    )


@pytest.mark.django_db
class TestBookingViews:

    def test_list_bookings_unauthenticated(self, api_client):
        """Неаутентифицированный пользователь не может просматривать список бронирований."""
        url = reverse("booking-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_bookings_authenticated(self, api_client, tenant_user, booking):
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-list")
        response = api_client.get(url)

        print("Response data:", response.data)

        assert response.status_code == 200

        data = response.data.get("data")
        # Если внутри 'data' есть вложенный 'data', берем его
        if data and isinstance(data, dict) and "data" in data:
            data = data["data"]

        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) >= 1

    # def test_list_bookings_authenticated(self, api_client, tenant_user, booking):
    #     api_client.force_authenticate(user=tenant_user)
    #     url = reverse('booking-list')
    #     response = api_client.get(url)
    #
    #     assert response.status_code == 200
    #     assert 'data' in response.data
    #     assert 'results' in response.data['data']
    #     # assert isinstance(response.data['data']['results'], list)
    #
    #     assert isinstance(response.data['data'], list)
    #     assert len(response.data['data']) >= 1

    def test_retrieve_booking_unauthenticated(self, api_client, booking):
        """Неаутентифицированный пользователь не может получить детали бронирования."""
        url = reverse("booking-detail", kwargs={"pk": booking.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_booking_owner(self, api_client, tenant_user, booking):
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-detail", kwargs={"pk": booking.pk})
        response = api_client.get(url)
        import json

        print("Response data JSON:", json.dumps(response.data, indent=4))

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert "data" in response.data["data"]
        assert "booking" in response.data["data"]["data"]

        booking_data = response.data["data"]["data"]["booking"]
        assert booking_data["id"] == booking.pk

    # def test_retrieve_booking_owner(self, api_client, tenant_user, booking):
    #     api_client.force_authenticate(user=tenant_user)
    #     url = reverse('booking-detail', kwargs={'pk': booking.pk})
    #     response = api_client.get(url)
    #     assert response.status_code == status.HTTP_200_OK
    #     booking_data = response.data['data']
    #     assert booking_data['id'] == booking.pk
    #     assert 'listing' not in response.data

    def test_retrieve_booking_not_owner_but_landlord(
        self, api_client, owner_user, listing
    ):
        tenant = User.objects.create_user(
            email="test_tenant@example.com", password="password", role="TENANT"
        )
        booking_for_owner_listing = Booking.objects.create(
            listing=listing,
            user=tenant,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=7),
            total_price=2 * listing.price_per_night,
            status="CONFIRMED",
        )

        api_client.force_authenticate(user=owner_user)
        url = reverse("booking-detail", kwargs={"pk": booking_for_owner_listing.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert "data" in response.data["data"]  # Вторая вложенность
        assert "booking" in response.data["data"]["data"]

        booking_data = response.data["data"]["data"]["booking"]
        assert booking_data["id"] == booking_for_owner_listing.pk
        assert float(booking_data["total_price"]) == 2 * listing.price_per_night

    def test_retrieve_booking_not_owner_and_not_landlord(
        self, api_client, another_tenant_user, another_landlord_user
    ):
        """Пользователь, не являющийся владельцем бронирования и не арендодателем, не может получить детали чужого бронирования."""
        another_listing = Listing.objects.create(
            title="Another Listing",
            description="Desc",
            user=another_landlord_user,
            price_per_night=100.0,
            address="456 Oak",
            city="London",
            country="UK",
            latitude=1.0,
            longitude=1.0,
            rooms=2.0,
            property_type="Apartment",
            availability={
                (date.today() + timedelta(days=1)).isoformat(): True,
                (date.today() + timedelta(days=2)).isoformat(): True,
            },
            is_active=True,
        )

        booking_start_date = date.today() + timedelta(days=1)
        booking_end_date = date.today() + timedelta(days=2)
        calculated_total_price = (
            booking_end_date - booking_start_date
        ).days * another_listing.price_per_night

        another_booking = Booking.objects.create(
            listing=another_listing,
            user=another_landlord_user,  # Владелец объявления делает бронирование
            start_date=booking_start_date,
            end_date=booking_end_date,
            total_price=calculated_total_price,
        )

        api_client.force_authenticate(user=another_tenant_user)
        url = reverse("booking-detail", kwargs={"pk": another_booking.pk})
        response = api_client.get(url)
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_create_booking_unauthenticated(self, api_client, listing):
        """Неаутентифицированный пользователь не может создать бронирование."""
        url = reverse("booking-list")
        data = {
            "listing": listing.pk,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_booking_valid_data(self, api_client, tenant_user, listing):
        """Создание бронирования арендатором с валидными данными."""
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-list")
        start_date = date.today() + timedelta(days=10)
        end_date = date.today() + timedelta(days=15)

        # Убедимся, что даты доступны в объявлении
        for i in range(10, 15):
            listing.availability[(date.today() + timedelta(days=i)).isoformat()] = True
        listing.save()

        data = {
            "listing": listing.pk,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        response = api_client.post(url, data, format="json")

        # ✅ Проверка успешного создания
        assert response.status_code == status.HTTP_201_CREATED

        # ✅ Проверка структуры ответа
        assert "data" in response.data
        assert "booking" in response.data["data"]
        booking_data = response.data["data"]["booking"]

        # ✅ Проверка, что объект создан в базе
        assert Booking.objects.filter(
            listing=listing, user=tenant_user, start_date=start_date, end_date=end_date
        ).exists()

        # ✅ Проверка ID (теперь через 'listing_data')
        assert booking_data["listing_data"]["id"] == listing.pk

        # ✅ Проверка total_price
        expected_total_price = (end_date - start_date).days * listing.price_per_night
        assert float(booking_data["total_price"]) == expected_total_price

    def test_create_booking_invalid_data(self, api_client, tenant_user, listing):
        """Попытка создать бронирование с невалидными данными (отсутствует listing)."""
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-list")
        data = {
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        # Исправлено: Ожидаем 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "listing" in response.data
        )  # Проверяем, что есть ошибка для поля 'listing'

    def test_create_booking_invalid_dates_end_before_start(
        self, api_client, tenant_user, listing
    ):
        """Попытка создать бронирование с некорректными датами (конец раньше начала)."""
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-list")
        data = {
            "listing": listing.pk,
            "start_date": (date.today() + timedelta(days=25)).isoformat(),
            "end_date": (date.today() + timedelta(days=20)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        # Исправлено: Ожидаем 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # assert 'non_field_errors' in response.data or 'end_date' in response.data
        assert "non_field_errors" in response.data
        assert any(
            "after start date" in err for err in response.data["non_field_errors"]
        )

    def test_create_booking_invalid_dates_past_start(
        self, api_client, tenant_user, listing
    ):
        """Попытка создать бронирование с датой начала в прошлом."""
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-list")
        data = {
            "listing": listing.pk,
            "start_date": (date.today() - timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        # Исправлено: Ожидаем 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "start_date" in response.data

    def test_create_booking_invalid_duration_too_long(
        self, api_client, tenant_user, listing
    ):
        """Попытка создать бронирование слишком длинной продолжительности (>30 дней)."""
        api_client.force_authenticate(user=tenant_user)
        url = reverse("booking-list")
        data = {
            "listing": listing.pk,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=32)).isoformat(),  # 31 день
        }
        response = api_client.post(url, data, format="json")
        # Исправлено: Ожидаем 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
