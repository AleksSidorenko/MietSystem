# tests/api/test_analytics.py
import pytest
from rest_framework import status
from analytics.models import ViewHistory
import json



@pytest.mark.django_db
def test_analytics_export_csv(api_client_admin, listing, tenant_user):
    ViewHistory.objects.create(user=tenant_user, listing=listing)
    response = api_client_admin.get('/api/analytics/export/')
    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    content = response.content.decode()
    assert listing.city in content


