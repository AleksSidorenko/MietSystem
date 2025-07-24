
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_landlord_can_create_listing(landlord_user, api_client):
    api_client.force_authenticate(user=landlord_user)
    url = reverse('listing-list')
    data = {'title': 'Test Listing', 'price_per_night': 50, 'rooms': 1, 'city': 'Berlin'}
    response = api_client.post(url, data)
    assert response.status_code == 201

@pytest.mark.django_db
def test_tenant_cannot_create_listing(tenant_user, api_client):
    api_client.force_authenticate(user=tenant_user)
    url = reverse('listing-list')
    data = {'title': 'Invalid Listing'}
    response = api_client.post(url, data)
    assert response.status_code == 403

@pytest.mark.django_db
def test_admin_can_delete_listing(admin_user, api_client, listing):
    api_client.force_authenticate(user=admin_user)
    url = reverse('listing-detail', args=[listing.id])
    response = api_client.delete(url)
    assert response.status_code in [200, 204]
