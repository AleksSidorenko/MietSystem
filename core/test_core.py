# core/test_core.py
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="testpassword",
        first_name="Admin",
        last_name="User",
    )

@pytest.mark.django_db
def test_health_check_api(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert response.json().get("data", {}).get("status", "").lower() == "ok"

@pytest.mark.django_db
def test_status_page_unauthenticated(client):
    client.logout()
    response = client.get(reverse("status"))
    # login_required should redirect unauthenticated -> login (302)
    assert response.status_code == 302
    assert response.url is not None


@pytest.mark.django_db
def test_status_page_authenticated(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("status"))
    assert response.status_code == 200
    content_decoded = response.content.decode()
    assert len(content_decoded) > 0


@pytest.mark.django_db
def test_status_page_localization(client, admin_user):
    client.force_login(admin_user)

    # English
    response_en = client.get(reverse("status"), HTTP_ACCEPT_LANGUAGE="en")
    assert response_en.status_code == 200
    content_en = response_en.content.decode()
    assert len(content_en) > 0

    # Russian
    response_ru = client.get(reverse("status"), HTTP_ACCEPT_LANGUAGE="ru")
    assert response_ru.status_code == 200
    content_ru = response_ru.content.decode()
    assert len(content_ru) > 0

    # German
    response_de = client.get(reverse("status"), HTTP_ACCEPT_LANGUAGE="de")
    assert response_de.status_code == 200
    content_de = response_de.content.decode()
    assert len(content_de) > 0


@pytest.mark.django_db
def test_status_page_data(client, admin_user):
    client.force_login(admin_user)
    response = client.get(reverse("status"))
    assert response.status_code == 200
    assert hasattr(response, "context") and response.context is not None
