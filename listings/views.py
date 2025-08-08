# listings/views.py
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import status, viewsets
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from listings.models import Listing
from listings.serializers import ListingSerializer
from listings.permissions import IsAdminOrLandlordOrReadOnly
from analytics.models import ViewHistory, SearchHistory


# ---------------------------
# 🔎 ФИЛЬТРЫ
# ---------------------------
class ListingFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price_per_night", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price_per_night", lookup_expr="lte")
    rooms = django_filters.NumberFilter(field_name="rooms")
    property_type = django_filters.CharFilter(field_name="property_type")
    amenities = django_filters.CharFilter(method="filter_amenities")

    def filter_amenities(self, queryset, name, value):
        amenities = value.split(",")
        return queryset.filter(amenities__contains=amenities)

    class Meta:
        model = Listing
        fields = ["price_min", "price_max", "rooms", "property_type", "amenities"]


# ---------------------------
# ✅ VIEWSET С ОГРАНИЧЕНИЯМИ
# ---------------------------
@method_decorator(ratelimit(key='ip', rate='100/m', method='POST', block=True), name='create')
@method_decorator(ratelimit(key='ip', rate='100/m', method='PUT', block=True), name='update')
@method_decorator(ratelimit(key='ip', rate='100/m', method='DELETE', block=True), name='destroy')
class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ListingFilter
    permission_classes = [IsAdminOrLandlordOrReadOnly]
    ordering_fields = ['price_per_night', 'created_at', 'popularity']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user

        # Для администраторов показываем все объявления, включая неактивные
        if user.is_authenticated and user.role == 'ADMIN':
            return Listing.objects.all().order_by('-created_at')

        # Для лендлордов показываем только их собственные объявления
        if user.is_authenticated and user.role == 'LANDLORD':
            return Listing.objects.filter(user=user).order_by('-created_at')

        # Для всех остальных (анонимных и TENANT) показываем только активные объявления
        return Listing.objects.filter(is_active=True).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # Мы убрали метод get_permissions(), так как IsAdminOrLandlordOrReadOnly
    # полностью покрывает необходимую логику доступа.

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user.is_authenticated:
            ViewHistory.objects.create(user=request.user, listing=instance)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        query = request.query_params.get("query", None)

        if query and request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, query=query)

        return super().list(request, *args, **kwargs)
