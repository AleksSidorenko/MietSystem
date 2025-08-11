# tests/api/test_users.py
import pytest
from django.urls import reverse
from bookings.models import Booking
from listings.models import Listing
from users.models import User
from datetime import date, timedelta



@pytest.mark.django_db
def test_admin_can_list_users(api_client_admin):
    response = api_client_admin.get(reverse('user-list'))
    assert response.status_code == 200
    assert 'results' in response.data['data']
    # assert isinstance(response.data, list) or 'results' in response.data


@pytest.mark.django_db
def test_tenant_lists_only_landlords_they_have_booked(api_client_tenant, tenant_user, landlord_user, listing, booking):
    api_client_tenant.force_authenticate(user=tenant_user)
    url = reverse('user-list')
    response = api_client_tenant.get(url)

    assert response.status_code == 200

    users_list = response.data.get('data', {}).get('results', [])

    landlord_ids = [user['id'] for user in users_list]

    assert landlord_user.id in landlord_ids

@pytest.mark.django_db
def test_tenant_can_update_self(api_client_tenant, tenant_user):
    url = reverse('user-me')
    data = {'first_name': 'Updated'}
    response = api_client_tenant.patch(url, data)
    assert response.status_code == 200
    tenant_user.refresh_from_db()
    assert tenant_user.first_name == 'Updated'

