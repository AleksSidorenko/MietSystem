# reviews/permissions.py
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission



class IsReviewOwnerOrAdmin(BasePermission):
    message = _("Only the review owner or admin can perform this action")

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user or (
            request.user.is_superuser or request.user.role == "ADMIN"
        )

class IsAdminOnly(BasePermission):
    message = _("Only admins can perform this action")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.role == "ADMIN")
        )

class IsTenant(BasePermission):
    message = _("Only tenants are allowed to perform this action.")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "role", None) == "TENANT"
        )