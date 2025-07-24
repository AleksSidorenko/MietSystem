### ✅ users/permissions.py

# from rest_framework.permissions import BasePermission, SAFE_METHODS
#
#
# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'ADMIN'
#
#
# class IsLandlord(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'LANDLORD'
#
#
# class IsTenant(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'TENANT'
#
#
# class IsSelfOrAdmin(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         return request.user == obj or request.user.role == 'ADMIN'
#
#
# class IsAuthenticated(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated

# # users/permissions.py
#
# from rest_framework.permissions import BasePermission, SAFE_METHODS
#
#
# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'ADMIN'
#
#
# class IsLandlord(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'LANDLORD'
#
#
# class IsTenant(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == 'TENANT'
#
#
# class IsSelfOrAdmin(BasePermission):
#     """
#     Доступ к пользователю:
#     - сам пользователь может просматривать/обновлять свой профиль
#     - админ может всё
#     """
#     def has_object_permission(self, request, view, obj):
#         return request.user == obj or request.user.role == 'ADMIN'
#
# class IsAuthenticated(BasePermission):
#     """Любой авторизованный пользователь"""
#     def has_permission(self, request, view):
#         return request.user.is_authenticated


# users/permissions.py

from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """Доступ только для админов"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "ADMIN"

class IsSelfOrAdmin(BasePermission):
    """Пользователь может менять себя, либо админ"""
    def has_object_permission(self, request, view, obj):
        return request.user == obj or (request.user.is_authenticated and request.user.role == "ADMIN")

class IsTenant(BasePermission):
    """Только TENANT"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "TENANT"

class IsLandlord(BasePermission):
    """Только LANDLORD"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "LANDLORD"

class IsAdmin(BasePermission):
    """Полные права для ADMIN"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == "ADMIN" or request.user.is_superuser
        )
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsAuthenticated(BasePermission):
    """Любой авторизованный пользователь"""
    def has_permission(self, request, view):
        return request.user.is_authenticated



# users/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "ADMIN"

class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj or (request.user.is_authenticated and request.user.role == "ADMIN")

class IsTenant(BasePermission):
    """
    Разрешает доступ только арендаторам.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "TENANT"

    def has_object_permission(self, request, view, obj):
        # Арендатор имеет права только на свои собственные объекты.
        # Например, для бронирования это означает, что арендатор может взаимодействовать
        # только со своими собственными бронированиями (obj.user == request.user).
        # Эту логику лучше вынести в IsBookingOwnerOrLandlord,
        # если IsTenant используется только для разрешения создания бронирований.
        # В данном случае, пока оставим его простым, если не требуется для других объектов.
        return True  # Или False, если IsTenant используется только для create/list, а не для деталей


class IsLandlord(BasePermission):
    """
    Разрешает доступ только арендодателям.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "LANDLORD"

    def has_object_permission(self, request, view, obj):
        # Арендодатель имеет права на свои объекты размещения и связанные с ними бронирования.
        # Здесь также может потребоваться специфическая логика для разных типов объектов.
        return True  # Или False


class IsAdmin(BasePermission):
    """
    Разрешает доступ только администраторам (роль ADMIN или is_superuser).
    Администраторы имеют полный доступ ко всем объектам.
    """

    def has_permission(self, request, view):
        # Администратор имеет общие разрешения, чтобы видеть все представления
        return request.user.is_authenticated and (
            request.user.role == "ADMIN" or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        # Администратор имеет полные права на уровне объекта.
        return request.user.is_authenticated and (
            request.user.role == "ADMIN" or request.user.is_superuser
        )


class IsAuthenticated(BasePermission):
    """
    Разрешает доступ только аутентифицированным пользователям.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Для базового IsAuthenticated, разрешения на уровне объекта обычно не требуются,
        # так как это разрешение обычно комбинируется с более специфичными.
        return True  # Или False, в зависимости от контекста


class IsBookingOwnerOrLandlord(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == "ADMIN":
            return True
        if obj.user == request.user:
            return True
        if obj.listing.user == request.user:
            return True
        return False
