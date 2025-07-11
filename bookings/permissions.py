### `bookings/permissions.py`

from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsBookingOwnerOrLandlord(permissions.BasePermission):
    """
    Владелец бронирования может читать/изменять.
    Арендодатель может читать бронирования своих объявлений.
    Только арендатор может создавать.
    """

    def has_permission(self, request, view):
        if request.method == "POST":
            # Только TENANT может создавать
            return request.user.is_authenticated and request.user.role == "TENANT"
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return (
                obj.user == request.user
                or obj.listing.user == request.user
                or request.user.is_staff
                or request.user.is_superuser
            )
        return (
            obj.user == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение для владельца объекта или администратора.
    """

    def has_object_permission(self, request, view, obj):
        return (
            obj.user == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )


class IsBookingOwnerOrLandlordOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user == obj.user or user == obj.listing.user or user.is_staff


class IsOwnerOrLandlordOrAdmin(permissions.BasePermission):
    """
    Разрешение для владельца, арендодателя (владельца объявления) или администратора.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        if hasattr(obj, "user") and obj.user == request.user:
            return True
        if (
            hasattr(obj, "listing")
            and hasattr(obj.listing, "user")
            and obj.listing.user == request.user
        ):
            return True
        return False
