# users/permissions.py
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
                request.user
                and request.user.is_authenticated
                and request.user.role == "ADMIN"
        )


class IsSelfOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj or (
                request.user.is_authenticated and request.user.role == "ADMIN"
        )


class IsTenant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "TENANT"

    def has_object_permission(self, request, view, obj):
        return True


class IsLandlord(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "LANDLORD"

    def has_object_permission(self, request, view, obj):
        return True


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
                request.user.role == "ADMIN" or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
                request.user.role == "ADMIN" or request.user.is_superuser
        )


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return True


class IsBookingOwnerOrLandlord(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == "ADMIN":
            return True
        if obj.user == request.user:
            return True
        if obj.listing.user == request.user:
            return True
        return False


class IsAdminOrLandlord(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.role in ['ADMIN', 'LANDLORD']

class ReviewPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        # Разрешаем всем просматривать список отзывов (list)
        if view.action == 'list' and request.method == 'GET':
            return True

        # Разрешаем доступ к деталям (retrieve) для аутентифицированных пользователей
        if view.action == 'retrieve' and request.method == 'GET':
            return user.is_authenticated

        # Разрешаем создавать отзывы только для аутентифицированных TENANT
        if view.action == 'create' and request.method == 'POST':
            return user.is_authenticated and user.role == "TENANT"

        return user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == "ADMIN":
            return True

        if view.action == 'approve':
            # Разрешаем одобрение администратору
            if user.role == "ADMIN":
                return True
            # Разрешаем одобрение лендлорду, если отзыв относится к его объявлению
            if user.role == "LANDLORD":
                return obj.booking.listing.user == user
            return False

        # Разрешаем просматривать детали отзыва (retrieve) для всех, у кого есть права
        if view.action == 'retrieve' and request.method == 'GET':
            return True

        # Разрешаем редактирование и удаление только владельцу отзыва
        if view.action in ['update', 'partial_update', 'destroy']:
            return obj.user == user

        return False
