# bookings/permissions.py
from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrOwnerOrLandlord(permissions.BasePermission):
    """
    Разрешает доступ администраторам, владельцам бронирования (tenant)
    и владельцам объявления (landlord).
    """

    def has_permission(self, request, view):
        # Admin может все.
        if request.user.is_staff or request.user.is_superuser:
            return True

        # POST-запросы (создание бронирования) разрешены только TENANT.
        if request.method == 'POST':
            return request.user.role == 'TENANT'

        # Всем остальным (GET, PUT, PATCH, DELETE) нужен has_object_permission.
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin может всё
        if user.is_staff or user.is_superuser:
            return True

        # GET-запросы: Tenant может смотреть свое бронирование, Landlord - бронирование своего объявления.
        if request.method in permissions.SAFE_METHODS:
            return (
                obj.user == user or  # Владелец бронирования (tenant)
                (user.role == "LANDLORD" and obj.listing.user == user)  # Владелец объявления (landlord)
            )

        # PUT, PATCH, DELETE: Владелец бронирования или Landlord могут редактировать.
        if request.method in ["PUT", "PATCH", "DELETE"]:
            return (
                obj.user == user or
                (user.role == "LANDLORD" and obj.listing.user == user)
            )

        return False

class IsBookingOwnerOrLandlord(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return request.user.is_authenticated and request.user.role == "TENANT"
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return (
                obj.user == request.user # <--- ИСПОЛЬЗУЕМ obj.user (владелец бронирования)
                or obj.listing.user == request.user # <--- ИСПОЛЬЗУЕМ obj.listing.user (владелец объявления)
                or request.user.is_staff
                or request.user.is_superuser
            )
        return (
            obj.user == request.user # <--- ИСПОЛЬЗУЕМ obj.user
            or request.user.is_staff
            or request.user.is_superuser
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Здесь "Owner" в контексте бронирования - это его создатель (tenant)
        return (
            obj.user == request.user # <--- ИСПОЛЬЗУЕМ obj.user (создатель бронирования)
            or request.user.is_staff
            or request.user.is_superuser
        )

class IsBookingOwnerOrLandlordOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # Этот класс называется "BookingOwnerOrLandlordOrAdmin",
        # так что он должен проверять владельца бронирования (tenant),
        # владельца объявления (landlord), и админа.

        return (
            obj.user == user  # Владелец бронирования (tenant)
            or obj.listing.user == user  # Владелец объявления (landlord)
            or user.is_staff  # Администратор (is_staff или is_superuser)
            or user.is_superuser
        )

class IsOwnerOrLandlordOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or user.is_superuser: # <--- Эти проверки ОК
            return True

        if obj.tenant == request.user: # obj.tenant - это пользователь, создавший бронирование
            return True

        if obj.listing.landlord == request.user: # Проверяем, является ли пользователь арендодателем объявления
            return True
        return False


class IsAdminOrOwnerOrLandlordOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Admin может всё
        if request.user.role == 'ADMIN':
            return True

        # POST только Tenant (или Admin)
        if request.method == 'POST':
            return request.user.role in ['TENANT', 'ADMIN']

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
                request.user.role == 'ADMIN' or  # Admin всё
                obj.tenant == request.user or  # Владелец бронирования
                obj.listing.user == request.user  # Владелец объявления
        )
