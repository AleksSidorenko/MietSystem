# tests/api/test_listings.py
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_landlord_can_create_listing(api_client_landlord, sample_listing_data, sample_amenities):
    url = reverse('listing-list')
    data = sample_listing_data.copy()
    # Передаём список имён, как их ждёт сериализатор
    data['amenities'] = [a.name for a in sample_amenities]
    response = api_client_landlord.post(url, data, format='json')

    print("Response data:", response.data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_tenant_cannot_create_listing(api_client_tenant, sample_listing_data):
    url = reverse('listing-list')
    response = api_client_tenant.post(url, sample_listing_data)
    assert response.status_code == 403

@pytest.mark.django_db
def test_admin_can_delete_listing(api_client_admin, listing):
    url = reverse('listing-detail', args=[listing.id])
    response = api_client_admin.delete(url)
    assert response.status_code in [200, 204]