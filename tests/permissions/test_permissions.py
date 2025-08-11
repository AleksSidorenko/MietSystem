# tests/permissions/test_permissions.py
import pytest
from rest_framework.test import APIRequestFactory
from users.permissions import IsTenant, IsLandlord
from users.models import User
from bookings.models import Booking

factory = APIRequestFactory()

@pytest.mark.django_db
def test_is_admin_permission(admin_user):
    request = factory.get("/")
    request.user = admin_user
    from users.permissions import IsAdmin
    assert IsAdmin().has_permission(request, None) is True
    request.user.role = "TENANT"
    assert IsAdmin().has_permission(request, None) is False

@pytest.mark.django_db
def test_booking_object_permission(booking, tenant_user, landlord_user):
    request = factory.get("/")
    # tenant can access own booking
    request.user = tenant_user
    assert IsTenant().has_object_permission(request, None, booking) is True
    # landlord (owner of listing) can access booking related to his listing
    request.user = landlord_user
    # ensure landlord_user is owner of listing for this test
    booking.listing.user = landlord_user
    booking.listing.save()
    assert IsLandlord().has_object_permission(request, None, booking) is True
