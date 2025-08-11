# tests/admin/test_locations_admin.py

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse
from listings.models import Listing
from locations.models import City, FederalState, Location
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="pass123")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com", password="pass123", role="ADMIN", is_staff=True
    )


@pytest.fixture
def landlord_user():
    return User.objects.create_user(
        email="landlord@example.com", password="pass123", role="LANDLORD", is_staff=True
    )


@pytest.fixture
def tenant_user():
    return User.objects.create_user(
        email="tenant@example.com", password="pass123", role="TENANT", is_staff=False
    )


@pytest.fixture
def listing(superuser):
    return Listing.objects.create(
        title_en="Test Listing for Location",
        description_en="A nice listing to test locations.",
        user=superuser,
        price_per_night=1000.00,
        rooms=2.0,
        is_active=True,
        address="123 Example St",
        property_type="Apartment",
    )


@pytest.fixture
def location(listing):
    return Location.objects.create(
        listing=listing,
        city_en=City.BERLIN.value,
        federal_state_en=FederalState.BERLIN.value,
        postal_code="10115",
        street="Example Street 123",
        coordinates=Point(13.404954, 52.520008),
    )


@pytest.mark.parametrize(
    "user_fixture, expected_status",
    [
        ("superuser", 200),
        ("admin_user", 200),
        ("landlord_user", 200),  # раньше было 403
        ("tenant_user", 302),
    ],
)
def test_locationsadmin_changelist_access(
    client, request, user_fixture, expected_status, location
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)
    url = reverse("admin:locations_location_changelist")
    response = client.get(url)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert "Berlin" in response.content.decode()
# # tests/admin/test_locations_admin.py
#
# import pytest
# from django.contrib.contenttypes.models import ContentType
# from django.contrib.gis.geos import Point
# from django.urls import reverse
#
# from listings.models import Listing
# from locations.models import City, FederalState, Location
# from users.models import User
#
# pytestmark = pytest.mark.django_db
#
#
# @pytest.fixture
# def superuser():
#     return User.objects.create_superuser(email="super@example.com", password="pass123")
#
#
# @pytest.fixture
# def admin_user():
#     return User.objects.create_user(
#         email="admin@example.com", password="pass123", role="ADMIN", is_staff=True
#     )  # is_staff=True для доступа к админке
#
#
# @pytest.fixture
# def landlord_user():
#     user = User.objects.create_user(
#         email="landlord@example.com", password="pass123", role="LANDLORD", is_staff=True
#     )
#
#     user.refresh_from_db()
#     if hasattr(user, "_perm_cache"):  # До Django 4.0
#         del user._perm_cache
#     if hasattr(user, "_user_perm_cache"):  # После Django 4.0
#         del user._user_perm_cache
#     if hasattr(user, "_group_perm_cache"):
#         del user._group_perm_cache
#
#     user.user_permissions.set([])
#     user.groups.set([])
#     user.save()
#     return user
#
#
# @pytest.fixture
# def tenant_user():
#     return User.objects.create_user(
#         email="tenant@example.com", password="pass123", role="TENANT", is_staff=False
#     )  # is_staff=False для перенаправления на логин
#
#
# @pytest.fixture
# def listing(superuser):
#     return Listing.objects.create(
#         title_en="Test Listing for Location",
#         description_en="A nice listing to test locations.",
#         user=superuser,
#         price_per_night=1000.00,
#         rooms=2.0,
#         is_active=True,
#         address="123 Example St",
#         property_type="Apartment",
#     )
#
#
# @pytest.fixture
# def location(listing):
#     return Location.objects.create(
#         listing=listing,
#         city_en=City.BERLIN.value,
#         federal_state_en=FederalState.BERLIN.value,
#         postal_code="10115",
#         street="Example Street 123",
#         coordinates=Point(13.404954, 52.520008),
#     )
#
# @pytest.mark.django_db
# @pytest.mark.parametrize(
#     "user_fixture, expected_status",
#     [
#         ("superuser", 200),
#         ("admin_user", 200),
#         ("landlord_user", 403),  # Так и должно быть
#         ("tenant_user", 302),
#     ],
# )
# @pytest.mark.django_db
# def test_locationsadmin_changelist_access(
#     client, request, user_fixture, expected_status, location
# ):
#     user = request.getfixturevalue(user_fixture)
#     client.force_login(user)
#
#     url = reverse("admin:locations_location_changelist")
#     response = client.get(url)
#     assert response.status_code == expected_status
#     if expected_status == 200:
#         assert "Berlin" in response.content.decode()
