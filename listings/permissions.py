# listings/permissions.py

from rest_framework import permissions

class IsAdminOrLandlordOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return view.action in ['list', 'retrieve']
        if request.user.role == 'ADMIN':
            return True
        if request.user.role == 'LANDLORD':
            return True
        if request.user.role == 'TENANT':
            return view.action in ['list', 'retrieve']
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        if request.user.role == 'LANDLORD':
            return obj.user == request.user
        if request.user.role == 'TENANT':
            return view.action in ['retrieve']
        return False
