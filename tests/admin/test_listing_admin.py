# tests/admin/test_listing_admin.py

import pytest
from django.urls import reverse
from listings.models import Listing
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def landlord_user():
    return User.objects.create_user(
        email="landlord@example.com", password="pass123", role="LANDLORD", is_staff=True
    )


@pytest.fixture
def other_landlord():
    return User.objects.create_user(
        email="otherlandlord@example.com", password="pass123", role="LANDLORD", is_staff=True
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="pass123")


@pytest.fixture
def listing(landlord_user):
    return Listing.objects.create(
        title_en="Test Listing",
        user=landlord_user,
        price_per_night=100,
        address="Berlin",
        rooms=3.0,
        is_active=True,
        popularity=5,
    )


@pytest.mark.parametrize(
    "user_fixture, can_access_all",
    [
        ("superuser", True),
        ("landlord_user", False),
    ],
)
def test_listingadmin_queryset_access(
    client, request, user_fixture, can_access_all, listing, other_landlord
):
    user = request.getfixturevalue(user_fixture)
    client.force_login(user)

    Listing.objects.create(
        title_en="Other Listing",
        user=other_landlord,
        price_per_night=150,
        address="Munich",
        rooms=2.5,
        is_active=True,
        popularity=10,
    )

    url = reverse("admin:listings_listing_changelist")
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    if can_access_all:
        assert "Test Listing" in content
        assert "Other Listing" in content
    else:
        assert "Test Listing" in content
        assert "Other Listing" not in content


def test_toggle_active_action(client, landlord_user, listing):
    client.force_login(landlord_user)
    url = reverse("admin:listings_listing_changelist")
    data = {"action": "toggle_active", "_selected_action": [listing.id]}
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    listing.refresh_from_db()
    assert listing.is_active is False


@pytest.mark.django_db
def test_export_top_listings_csv(client, superuser, landlord_user):
    client.force_login(superuser)
    for i in range(10):
        Listing.objects.create(
            title_en=f"Listing {i}",
            title_de=f"Listing DE {i}",  # добавил
            user=landlord_user,
            price_per_night=50 + i,
            address=f"City_{i}",
            rooms=2.0,
            is_active=True,
            popularity=i,
        )

    url = reverse("admin:listings_listing_changelist")
    selected_ids = Listing.objects.values_list("id", flat=True)
    data = {
        "action": "export_top_listings",
        "_selected_action": list(map(str, selected_ids)),
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert "text/csv" in response["Content-Type"]
    content = response.content.decode()
    assert "Title (DE)" in content
    assert any(f"Listing DE {i}" in content for i in range(10))


def test_listingadmin_search(client, superuser, landlord_user):
    client.force_login(superuser)
    Listing.objects.create(
        title_en="UniqueTitleSearchTest",
        user=landlord_user,
        price_per_night=120,
        address="Hamburg",
        rooms=4.0,
        is_active=True,
        popularity=3,
    )
    url = reverse("admin:listings_listing_changelist")
    response = client.get(url, {"q": "UniqueTitleSearchTest"})
    assert response.status_code == 200
    assert "UniqueTitleSearchTest" in response.content.decode()


def test_listingadmin_permissions(
    client, landlord_user, superuser, listing, other_landlord
):
    client.force_login(superuser)
    url_change = reverse("admin:listings_listing_change", args=[listing.id])
    assert client.get(url_change).status_code == 200

    client.force_login(landlord_user)
    assert client.get(url_change).status_code == 200

    other_listing = Listing.objects.create(
        title_en="Other Listing",
        user=other_landlord,
        price_per_night=200,
        address="Cologne",
        rooms=3.5,
        is_active=True,
        popularity=1,
    )
    url_other = reverse("admin:listings_listing_change", args=[other_listing.id])
    resp = client.get(url_other)
    assert resp.status_code in (403, 302)
