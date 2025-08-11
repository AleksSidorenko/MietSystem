# tests/core/test_multilanguage.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_api_listings_multilanguage(api_client_tenant, listing):
    url = reverse('listing-detail', kwargs={'pk': listing.pk})

    response_en = api_client_tenant.get(url, HTTP_ACCEPT_LANGUAGE='en')
    assert response_en.status_code == 200

    response_ru = api_client_tenant.get(url, HTTP_ACCEPT_LANGUAGE='ru')
    assert response_ru.status_code == 200

    response_de = api_client_tenant.get(url, HTTP_ACCEPT_LANGUAGE='de')
    assert response_de.status_code == 200
