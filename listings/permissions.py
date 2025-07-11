### `listings/permissions.py`

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission


class IsListingOwner(BasePermission):
    message = _("Only the listing owner can perform this action")

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user


class IsLandlord(BasePermission):
    message = _("Only landlords can perform this action")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == "LANDLORD"
        )


# from rest_framework.permissions import BasePermission
#
# class IsListingOwner(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return request.user == obj.user
#
# class IsLandlord(BasePermission):
#     """
#     Разрешение, проверяющее, является ли пользователь арендодателем.
#     Предполагается, что модель User имеет поле role с значением 'LANDLORD'.
#     """
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'LANDLORD'
