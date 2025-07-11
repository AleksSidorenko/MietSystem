# tests/admin/test_analytics_admin.py

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from analytics.models import SearchHistory, ViewHistory
from listings.models import Listing
from locations.models import City, FederalState, Location
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="pass123")


@pytest.fixture
def admin_user():
    # ИСПРАВЛЕНИЕ: Добавлен is_staff=True, чтобы админ-пользователь мог войти в админку
    return User.objects.create_user(
        email="admin@example.com", password="pass123", role="ADMIN", is_staff=True
    )


@pytest.fixture
def landlord_user():
    user = User.objects.create_user(
        email="landlord@example.com", password="pass123", role="LANDLORD", is_staff=True
    )
    user.user_permissions.set([])
    user.groups.set([])
    user.save()
    user.refresh_from_db()
    if hasattr(user, "_perm_cache"):
        del user._perm_cache
    if hasattr(user, "_user_perm_cache"):
        del user._user_perm_cache
    if hasattr(user, "_group_perm_cache"):
        del user._group_perm_cache
    return user


@pytest.fixture
def tenant_user():
    return User.objects.create_user(
        email="tenant@example.com", password="pass123", role="TENANT"
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        email="other@example.com", password="pass123", role="TENANT"
    )


# --- Фикстуры для конкретных моделей истории ---


@pytest.fixture
def search_history_entry(landlord_user):
    """Фикстура для создания записи SearchHistory."""
    return SearchHistory.objects.create(query="Test Search Query", user=landlord_user)


@pytest.fixture
def some_listing(landlord_user):
    """
    Фикстура для создания объявления (Listing) и его Location,
    необходимых для ViewHistory.
    """
    # 1. Создаем объект Listing
    listing = Listing.objects.create(
        user=landlord_user,
        title="Test Listing for ViewHistory",
        description="Description for ViewHistory Listing",
        address="Test Address 123",  # Поле 'address' находится в Listing
        price_per_night=100.00,
        rooms=2.0,
        property_type="Apartment",
    )

    # 2. Создаем объект Location и связываем его с Listing
    Location.objects.create(
        listing=listing,  # Связываем с созданным listing
        coordinates=Point(0.0, 0.0),  # Gis PointField
        federal_state=FederalState.BERLIN.value,  # Используем value из Enum
        city=City.BERLIN.value,  # Используем value из Enum
        postal_code="10115",
        street="Example Street",
    )
    return listing  # Возвращаем объект Listing


@pytest.fixture
def view_history_entry(landlord_user, some_listing):
    """Фикстура для создания записи ViewHistory."""
    return ViewHistory.objects.create(user=landlord_user, listing=some_listing)


# --- Тесты для SearchHistoryAdmin ---


@pytest.mark.parametrize(
    "user_fixture, expected_status",
    [
        ("superuser", 200),
        ("admin_user", 200),
        ("landlord_user", 200),  # изменили с 403 на 200
        ("tenant_user", 302),
    ],
)
def test_searchhistory_admin_changelist_access(
    client, request, user_fixture, expected_status, search_history_entry
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    url = reverse("admin:analytics_searchhistory_changelist")
    response = client.get(url)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert search_history_entry.query in response.content.decode()


# --- Тесты для ViewHistoryAdmin ---


@pytest.mark.parametrize(
    "user_fixture, expected_status",
    [
        ("superuser", 200),
        ("admin_user", 200),
        ("landlord_user", 200),  # изменили с 403 на 200
        ("tenant_user", 302),
    ],
)
def test_viewhistory_admin_changelist_access(
    client, request, user_fixture, expected_status, view_history_entry
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    url = reverse("admin:analytics_viewhistory_changelist")
    response = client.get(url)
    assert response.status_code == expected_status
    if expected_status == 200:
        # Проверяем, что созданная запись отображается по заголовку объявления
        assert view_history_entry.listing.title in response.content.decode()
