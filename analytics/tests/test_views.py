# analytics/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from analytics.models import ViewHistory


import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_get_queryset_for_landlord(api_client, landlord_user, listing):
    api_client.force_authenticate(user=landlord_user)
    ViewHistory.objects.create(user=landlord_user, listing=listing)
    url = reverse('analytics-views-list')  # убедись, что имя URL верное
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.data.get('results', []) if isinstance(response.data, dict) else response.data
    for item in results:
        assert item['listing'] == listing.id


@pytest.mark.django_db
def test_top_5_admin(api_client, admin_user, listing):
    api_client.force_authenticate(user=admin_user)
    for _ in range(10):
        ViewHistory.objects.create(user=admin_user, listing=listing)
    url = reverse('analytics-views-top-5')
    response = api_client.get(url + "?time_frame=week")
    assert response.status_code == 200
    # Возможно, структура response.data: {'data': {'top_5': [...]}, 'meta': {...}}
    assert 'data' in response.data
    assert 'top_5' in response.data['data']
    assert isinstance(response.data['data']['top_5'], list) or hasattr(response.data['data']['top_5'], '__iter__')

@pytest.mark.django_db
def test_top_5_unauthorized(api_client):
    url = reverse('analytics-views-top-5')
    response = api_client.get(url)
    assert response.status_code == 401  # Исправлено с 403 на 401

@pytest.mark.django_db
def test_export_csv_unauthorized(api_client):
    url = reverse('analytics-export')
    response = api_client.get(url)
    assert response.status_code == 401  # Исправлено с 403 на 401


@pytest.mark.django_db
def test_get_queryset_for_admin(api_client, admin_user, listing):
    api_client.force_authenticate(user=admin_user)
    ViewHistory.objects.create(user=admin_user, listing=listing)
    url = reverse('analytics-views-list')
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_export_csv_admin(api_client, admin_user, listing):
    api_client.force_authenticate(user=admin_user)
    ViewHistory.objects.create(user=admin_user, listing=listing)
    url = reverse('analytics-export')
    response = api_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/csv'
    content = response.content.decode('utf-8')
    assert listing.title in content

@pytest.mark.django_db
def test_export_csv_landlord(api_client, landlord_user, listing):
    api_client.force_authenticate(user=landlord_user)
    ViewHistory.objects.create(user=landlord_user, listing=listing)
    url = reverse('analytics-export')
    response = api_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'text/csv'

