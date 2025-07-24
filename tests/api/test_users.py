
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_admin_can_list_users(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    url = reverse('user-list')  # Убедись, что имя роута указано верно.
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_admin_can_list_users(admin_user, api_client):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get(reverse('user-list'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_tenant_cannot_list_users(tenant_user, api_client):
    api_client.force_authenticate(user=tenant_user)
    response = api_client.get(reverse('user-list'))
    assert response.status_code == 403

@pytest.mark.django_db
def test_tenant_can_update_self(tenant_user, api_client):
    api_client.force_authenticate(user=tenant_user)
    url = reverse('user-me')
    data = {'first_name': 'Updated'}
    response = api_client.patch(url, data)
    assert response.status_code == 200
    assert response.data['first_name'] == 'Updated'

