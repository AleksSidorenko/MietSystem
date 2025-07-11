# tests/conftest.py

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from bookings.models import Booking
from listings.models import Listing

User = get_user_model()


@pytest.fixture
def landlord_user(db):
    """
    Создает пользователя, который будет владельцем объявления,
    с ролью 'LANDLORD'.
    """
    return User.objects.create_user(
        email="landlord@example.com",
        password="testpassword",
        first_name="John",  # REQUIRED_FIELDS для User
        last_name="Doe",  # REQUIRED_FIELDS для User
        role="LANDLORD",  # Используем поле 'role'
        is_verified=True,  # Для удобства в тестах можно сразу верифицировать
    )


@pytest.fixture
def tenant_user(db):
    """
    Создает пользователя-арендатора.
    """
    return User.objects.create_user(
        email="tenant@example.com",
        password="testpassword",
        first_name="Jane",
        last_name="Smith",
        role="TENANT",
        is_verified=True,
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_user(
        email="super@example.com",
        password="testpass",
        role="ADMIN",
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def admin_user(db):
    """
    Создает пользователя-администратора.
    """
    return User.objects.create_superuser(
        email="admin@example.com",
        password="testpassword",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def regular_user(db):  # Эта фикстура, возможно, не нужна, если tenant_user ее заменяет.
    # Но оставлю, так как она у вас была.
    return User.objects.create_user(
        email="user@example.com", password="testpass", role="TENANT"
    )


# --- НОВЫЕ/ПРОВЕРЕННЫЕ ФИКСТУРЫ ---
@pytest.fixture
def api_client():
    """Фикстура для DRF APIClient с отключенной проверкой CSRF."""
    client = APIClient()
    # Эта строка критична
    client.enforce_csrf_checks = False
    return client


@pytest.fixture
def listing(landlord_user):
    """
    Фикстура для объявления.
    Владельцем объявления является landlord_user.
    """
    return Listing.objects.create(
        user=landlord_user,
        title="Cozy Apartment in City Center",
        description="A beautifully furnished apartment.",
        address="123 Main St, Metropolis, Countryland",
        price_per_night=120.00,
        rooms=2.5,
        property_type="Apartment",
        amenities=["WiFi", "Kitchen"],
        photos=["photo1.jpg", "photo2.jpg"],
        is_active=True,
        popularity=0,
        availability={
            (date.today() + timedelta(days=i)).isoformat(): True for i in range(1, 60)
        },
    )


# @pytest.fixture
# def api_client():
#     """Фикстура для DRF APIClient с отключенной проверкой CSRF."""
#     client = APIClient()
#     # ЭТА СТРОКА ОЧЕНЬ ВАЖНА
#     client.enforce_csrf_checks = False
#     return client


@pytest.fixture
def booking(listing, tenant_user):
    """
    Фикстура для бронирования.
    Привязывается к фикстуре listing и tenant_user.
    """
    return Booking.objects.create(
        listing=listing,
        user=tenant_user,  # Используем 'user'
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=15),
        total_price=5 * listing.price_per_night,  # Корректный расчет цены
        status="PENDING",
    )
