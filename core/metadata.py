# core/metadata.py
from rest_framework.metadata import SimpleMetadata


class RoleAwareMetadata(SimpleMetadata):
    """
    Управляет отображением доступных операций в DRF панели в зависимости от роли пользователя.
    """

    def determine_actions(self, request, view):
        actions = super().determine_actions(request, view)
        user = request.user


        if not user or not user.is_authenticated:
            return {}  # Гости не видят действий

        role = getattr(user, "role", None)
        view_name = getattr(view, 'basename', None) or view.__class__.__name__.lower()

        if view_name in ('user', 'users', 'userviewset'):
            if role == "ADMIN":
                return actions  # Полный доступ, показывать всё

            if role == "LANDLORD" or role == "TENANT":
                # Оставить только 'me' и 'totp' в Extra Actions
                allowed = ['GET', 'OPTIONS', 'HEAD']
                extra_actions_allowed = ['me', 'totp']

                filtered_actions = {
                    method: url for method, url in actions.items()
                    if method in allowed or any(name in url for name in extra_actions_allowed)
                }
                return filtered_actions

        # Полный доступ для ADMIN
        if role == "ADMIN" or user.is_superuser:
            return actions

        # Landlord
        if role == "LANDLORD":
            if view_name in ('user', 'users', 'userviewset'):
                # Только чтение (видит Tenants своих бронирований)
                allowed = {'GET', 'OPTIONS', 'HEAD'}
                return {method: url for method, url in actions.items() if method in allowed}

            elif view_name in ('listing', 'listings', 'listingviewset'):
                # Полный доступ к своим объявлениям
                return actions

            elif view_name in ('booking', 'bookings', 'bookingviewset'):
                # Полный доступ к бронированиям своих объявлений
                return actions

            elif view_name in ('review', 'reviews', 'reviewviewset'):
                # Управление отзывами на свои объявления
                return actions

            else:
                # По умолчанию — только просмотр
                allowed = {'GET', 'OPTIONS', 'HEAD'}
                return {method: url for method, url in actions.items() if method in allowed}

        # Tenant
        if role == "TENANT":
            if view_name in ('user', 'users', 'userviewset'):
                # Только просмотр Landlords + изменение себя
                allowed = {'GET', 'PUT', 'PATCH', 'OPTIONS', 'HEAD'}
                return {method: url for method, url in actions.items() if method in allowed}

            elif view_name in ('listing', 'listings', 'listingviewset'):
                # Только просмотр объявлений
                allowed = {'GET', 'OPTIONS', 'HEAD'}
                return {method: url for method, url in actions.items() if method in allowed}

            elif view_name in ('booking', 'bookings', 'bookingviewset'):
                # CRUD по своим бронированиям
                return actions

            elif view_name in ('review', 'reviews', 'reviewviewset'):
                # CRUD по своим отзывам
                return actions

            else:
                # По умолчанию — просмотр
                allowed = {'GET', 'OPTIONS', 'HEAD'}
                return {method: url for method, url in actions.items() if method in allowed}

        return {}  # Для всех остальных — ничего
