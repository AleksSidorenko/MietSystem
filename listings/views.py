### `listings/views.py`

import django_filters
from django.core.cache import cache
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from users.permissions import IsAuthenticated

from .models import Listing
from .permissions import IsLandlord, IsListingOwner
from .serializers import ListingSerializer


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
    queryset = Listing.objects.filter(is_active=True)
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ListingFilter
    ordering_fields = ["price_per_night", "created_at", "popularity"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [IsAuthenticated(), IsLandlord()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsListingOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        cache_key = f"listings_{self.request.user.id}_{self.request.query_string}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        queryset = super().get_queryset()
        query = self.request.query_params.get("q")
        if query:
            queryset = queryset.filter(
                Q(title_en__icontains=query)
                | Q(title_de__icontains=query)
                | Q(title_ru__icontains=query)
                | Q(description_en__icontains=query)
                | Q(description_de__icontains=query)
                | Q(description_ru__icontains=query)
            )
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        cache.set(cache_key, queryset, timeout=3600)
        return queryset

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        cache_key = f"listings_{request.user.id}_"
        cache.delete_pattern(f"{cache_key}*")
        return response

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        cache_key = f"listings_{request.user.id}_"
        cache.delete_pattern(f"{cache_key}*")
        return response

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        cache_key = f"listings_{request.user.id}_"
        cache.delete_pattern(f"{cache_key}*")
        return Response(
            {"message": _("Listing deleted successfully")}, status=status.HTTP_200_OK
        )


# from rest_framework import viewsets
# from django.db.models import Q
# from django.core.cache import cache
# from .models import Listing
# from .serializers import ListingSerializer
# from rest_framework.permissions import IsAuthenticated
# from .permissions import IsLandlord, IsListingOwner
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import OrderingFilter
# import django_filters
#
# class ListingFilter(django_filters.FilterSet):
#     price_min = django_filters.NumberFilter(field_name='price_per_night', lookup_expr='gte')
#     price_max = django_filters.NumberFilter(field_name='price_per_night', lookup_expr='lte')
#     rooms = django_filters.NumberFilter(field_name='rooms')
#     property_type = django_filters.CharFilter(field_name='property_type')
#     city = django_filters.CharFilter(field_name='city')
#     federal_state = django_filters.CharFilter(field_name='federal_state')
#     amenities = django_filters.CharFilter(method='filter_amenities')
#
#     def filter_amenities(self, queryset, name, value):
#         amenities = value.split(',')
#         return queryset.filter(amenities__contains=amenities)
#
#     class Meta:
#         model = Listing
#         fields = ['price_min', 'price_max', 'rooms', 'property_type', 'city', 'federal_state', 'amenities']
#
# class ListingViewSet(viewsets.ModelViewSet):
#     queryset = Listing.objects.filter(is_active=True)
#     serializer_class = ListingSerializer
#     permission_classes = [IsAuthenticated, IsLandlord]  # Добавляем IsLandlord
#     filter_backends = [DjangoFilterBackend, OrderingFilter]
#     filterset_class = ListingFilter
#     ordering_fields = ['price_per_night', 'created_at', 'popularity']
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         query = self.request.query_params.get('q')
#         if query:
#             queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
#         cache_key = f'listings_{self.request.query_string}'
#         cached = cache.get(cache_key)
#         if cached:
#             return cached
#         cache.set(cache_key, queryset, timeout=3600)
#         return queryset
#
#     def perform_create(self, serializer):
#         if self.request.user.role != 'LANDLORD':
#             raise serializers.ValidationError("Only landlords can create listings")
#         serializer.save(user=self.request.user)
#
#     def get_permissions(self):
#         if self.action in ['update', 'partial_update', 'destroy']:
#             return [IsAuthenticated(), IsListingOwner()]  # Только владелец может редактировать/удалять
#         return super().get_permissions()
