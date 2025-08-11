# bookings/tests/conftest.py

import pytest

from tests.conftest import (
    landlord_user,
    tenant_user,
    admin_user,
    superuser,
    listing,
    booking,
    api_client,
    api_client_landlord,
    api_client_tenant,
    api_client_admin,
    api_client_superuser,
)

@pytest.fixture
def booking_with_custom_status(booking):
    booking.status = "CONFIRMED"
    booking.save()
    return booking
