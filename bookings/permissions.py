# bookings/permissions.py
from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrOwnerOrLandlord(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == "ADMIN":
            return True

        if request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS
            if user.role == "LANDLORD":  # Владелец объявления (Landlord)
                # Может просматривать бронирования своих объявлений
                return obj.listing.user == user  # <--- ИСПОЛЬЗУЕМ obj.listing.user

            if user.role == "TENANT":  # Арендатор (создатель бронирования)
                # Может просматривать свои бронирования
                return obj.user == user  # <--- ИСПОЛЬЗУЕМ obj.user

        if request.method in ["PUT", "PATCH", "DELETE"]:
            # В зависимости от вашей бизнес-логики:
            # 1. Только арендатор может изменять/отменять СВОЕ бронирование.
            # 2. Арендодатель или администратор могут изменять/отменять бронирование, связанное с ИХ объявлением/системой.

            # Предполагаем, что владелец бронирования (арендатор) может изменять/удалять
            # и владелец объявления (арендодатель) также может изменять/удалять бронирование СВОЕГО объявления.
            # И, конечно, админ.
            return (
                    obj.user == user or  # Пользователь, создавший бронирование (арендатор)
                    (user.role == "LANDLORD" and obj.listing.user == user) or  # Владелец объявления (арендодатель)
                    user.role == "ADMIN"  # Администратор
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
