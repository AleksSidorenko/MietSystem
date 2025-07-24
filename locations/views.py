# locations/views.py

from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin, IsAuthenticated

from .models import Location
from .serializers import LocationSerializer


class IsOwnerOrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == "ADMIN"
        ):
            return True
        return request.user.is_authenticated and request.user.role == "LANDLORD"

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == "ADMIN":
            return True
        return obj.listing.user == request.user


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            return self.queryset
        return self.queryset.filter(listing__user=self.request.user)

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        serializer_class.Meta.swagger_schema_fields = {
            "description": "API for managing location data for listings",
        }
        return serializer_class

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        location_id = response.data.get("id")
        if location_id:
            from .tasks import geocode_address

            geocode_address.delay(location_id)
        return response

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def nearby(self, request):
        latitude = float(request.query_params.get("latitude", 0))
        longitude = float(request.query_params.get("longitude", 0))
        radius = float(request.query_params.get("radius", 10))  # km
        locations = self.queryset.filter(
            latitude__range=(latitude - radius / 111, latitude + radius / 111),
            longitude__range=(longitude - radius / 111, longitude + radius / 111),
        )
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

