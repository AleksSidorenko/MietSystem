#### `analytics/views.py`

import csv
from datetime import timedelta

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin, IsAuthenticated

from .models import SearchHistory, ViewHistory
from .serializers import SearchHistorySerializer, ViewHistorySerializer


class AnalyticsViewSet(viewsets.ModelViewSet):
    queryset = ViewHistory.objects.all()
    serializer_class = ViewHistorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "listing", "timestamp"]

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        serializer_class.Meta.swagger_schema_fields = {
            "description": "API for analyzing view and search history"
        }
        return serializer_class

    @action(detail=False, methods=["get"])
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def top_5(self, request):
        time_frame = request.query_params.get("time_frame", "week")
        if time_frame not in ["week", "month"]:
            return Response(
                {"error": _("Invalid time frame. Use 'week' or 'month'")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        start_date = timezone.now() - timedelta(days=7 if time_frame == "week" else 30)
        top_listings = (
            ViewHistory.objects.filter(timestamp__gte=start_date)
            .values("listing__title")
            .annotate(count=Count("listing"))
            .order_by("-count")[:5]
        )
        return Response({"top_5": top_listings})

    @action(detail=False, methods=["get"])
    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def export_csv(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="analytics_{timezone.now().date()}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow([_("Listing ID"), _("Title"), _("Views"), _("Timestamp")])
        views = ViewHistory.objects.select_related("listing").all()
        for view in views:
            writer.writerow([view.listing.id, view.listing.title, 1, view.timestamp])
        return response


class SearchHistoryViewSet(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.all()
    serializer_class = SearchHistorySerializer
    permission_classes = []

    def get_permissions(self):
        if self.action in ["list", "retrieve", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdmin()]
        return []

    @csrf_protect
    @ratelimit(group="ip", rate="100/m")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)
        if user:
            SearchHistory.objects.filter(user=user).order_by("-timestamp")[10:].delete()


# from rest_framework import viewsets
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from django.utils import timezone
# from datetime import timedelta
# from django.db.models import Count
# from django.http import HttpResponse
# import csv
# from .models import SearchHistory, ViewHistory
# from .serializers import SearchHistorySerializer, ViewHistorySerializer
# from users.permissions import IsAdmin
#
# class AnalyticsViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAdmin]
#
#     @action(detail=False, methods=['get'])
#     def top_5(self, request):
#         time_frame = request.query_params.get('time_frame', 'week')
#         if time_frame == 'week':
#             start_date = timezone.now() - timedelta(days=7)
#         else:
#             start_date = timezone.now() - timedelta(days=30)
#         top_listings = ViewHistory.objects.filter(
#             timestamp__gte=start_date
#         ).values('listing__title').annotate(count=Count('listing')).order_by('-count')[:5]
#         return Response({'top_5': top_listings})
#
#     @action(detail=False, methods=['get'])
#     def export_csv(self, request):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="analytics.csv"'
#         writer = csv.writer(response)
#         writer.writerow(['Listing ID', 'Title', 'Views', 'Timestamp'])
#         views = ViewHistory.objects.select_related('listing').all()
#         for view in views:
#             writer.writerow([view.listing.id, view.listing.title, 1, view.timestamp])
#         return response
#
# class SearchHistoryViewSet(viewsets.ModelViewSet):
#     queryset = SearchHistory.objects.all()
#     serializer_class = SearchHistorySerializer
#     permission_classes = [IsAdmin]
#
#     def perform_create(self, serializer):
#         user = self.request.user
#         if user.is_authenticated:
#             SearchHistory.objects.filter(user=user).order_by('-timestamp')[10:].delete()
#         serializer.save(user=user if user.is_authenticated else None)
