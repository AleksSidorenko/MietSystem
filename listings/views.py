# listings/views.py
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit

from bookings.permissions import IsOwnerOrAdmin
from listings.models import Listing
# from listings.permissions import IsLandlord, IsListingOwner
from listings.serializers import ListingSerializer
from users.permissions import IsAdmin, IsLandlord, IsTenant

from rest_framework import viewsets, permissions
from .models import Listing
from .serializers import ListingSerializer
from .permissions import IsAdminOrLandlordOrReadOnly


class ListingFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(
        field_name="price_per_night", lookup_expr="gte"
    )
    price_max = django_filters.NumberFilter(
        field_name="price_per_night", lookup_expr="lte"
    )
    rooms = django_filters.NumberFilter(field_name="rooms")
    property_type = django_filters.CharFilter(field_name="property_type")
    amenities = django_filters.CharFilter(method="filter_amenities")

    def filter_amenities(self, queryset, name, value):
        amenities = value.split(",")
        return queryset.filter(amenities__contains=amenities)

    class Meta:
        model = Listing
        fields = ["price_min", "price_max", "rooms", "property_type", "amenities"]

class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsAdminOrLandlordOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        if user.is_anonymous or user.role == 'TENANT':
            return Listing.objects.filter(is_active=True)

        if user.role == 'LANDLORD':
            return Listing.objects.filter(user=user)

        if user.role == 'ADMIN':
            return Listing.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if not hasattr(self, 'request') or self.request is None:
            return [IsAuthenticated()]  # ← позволяет drf-spectacular сгенерировать схему без авторизации

        if self.action == 'create':
            return [IsAuthenticated(), IsTenant()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]

        return [IsAuthenticated()]

    def get_user_role(self):
        return getattr(self.request.user, "role", None)

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Тут можно добавить очистку кэша, если есть
        return response

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Очистка кэша при обновлении
        return response

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        # Очистка кэша при удалении
        return response
