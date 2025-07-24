# tests/conftest.py

from datetime import date, timedelta
import pytest
from rest_framework.test import APIClient  # Убедитесь, что это импортировано!
from bookings.models import Booking
from listings.models import Listing
from users.models import User


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
    return User.objects.create_user(
        email="admin@example.com",
        password="testpass",
        role="ADMIN",
        is_staff=True,
    )


@pytest.fixture
def landlord_user(db):
    return User.objects.create_user(
        email="landlord@example.com",
        password="testpass",
        role="LANDLORD",
        is_staff=True,
    )


@pytest.fixture
def tenant_user(db):
    return User.objects.create_user(
        email="tenant@example.com", password="testpass", role="TENANT"
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
    """Фикстура для DRF APIClient."""
    return APIClient()


@pytest.fixture
def listing(landlord_user):
    """
    Фикстура для объявления.
    Владельцем объявления является landlord_user.
    Убедитесь, что Listing.objects.create имеет все необходимые поля
    в соответствии с вашей моделью Listing.
    """
    return Listing.objects.create(
        owner=landlord_user,
        title="Cozy Apartment in City Center",
        description="A beautifully furnished apartment.",
        price_per_night=120.00,
        address="123 Main St",
        city="Metropolis",
        country="Countryland",
        max_guests=3,
        is_active=True,
        availability={  # Пример доступности
            (date.today() + timedelta(days=i)).isoformat(): True
            for i in range(1, 60)  # Доступно на 60 дней вперед
        },
        # Добавьте любые другие обязательные поля вашей модели Listing
    )


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
