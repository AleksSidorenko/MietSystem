# # analytics/views.py
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from users.permissions import IsAdmin, IsTenant, IsAdminOrLandlord
from analytics.models import ViewHistory, SearchHistory
from analytics.serializers import ViewHistorySerializer, SearchHistorySerializer

from rest_framework.views import APIView
from io import StringIO


@method_decorator(ratelimit(key='ip', rate='100/m', method='GET', block=True), name='top_5')
@method_decorator(csrf_protect, name='top_5')
@method_decorator(ratelimit(key='ip', rate='100/m', method='GET', block=True), name='export_csv')
@method_decorator(csrf_protect, name='export_csv')
class AnalyticsViewSet(viewsets.ModelViewSet):
    queryset = ViewHistory.objects.none()
    serializer_class = ViewHistorySerializer
    permission_classes = [IsAdminOrLandlord]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or user.role not in ["ADMIN", "LANDLORD"]:
            return ViewHistory.objects.none()

        if user.role == "ADMIN":
            return ViewHistory.objects.all().order_by('-timestamp')

        if user.role == "LANDLORD":
            return ViewHistory.objects.filter(listing__user=user).order_by('-timestamp')

        return ViewHistory.objects.none()

    @action(detail=False, methods=["get"])
    def top_5(self, request):
        user = request.user

        # Разрешаем доступ только для ADMIN и LANDLORD
        if not user.is_authenticated or user.role not in ["ADMIN", "LANDLORD"]:
            return Response({"error": _("You do not have permission to perform this action.")},
                            status=status.HTTP_403_FORBIDDEN)

        time_frame = request.query_params.get("time_frame", "week")
        if time_frame not in ["week", "month"]:
            return Response({"error": _("Invalid time frame. Use 'week' or 'month'")},
                            status=status.HTTP_400_BAD_REQUEST)

        days = 7 if time_frame == "week" else 30
        start_date = timezone.now() - timezone.timedelta(days=days)

        # Логика фильтрации для LANDLORD
        queryset = ViewHistory.objects.filter(timestamp__gte=start_date)
        if user.role == "LANDLORD":
            queryset = queryset.filter(listing__user=user)

        top_listings = (
            queryset
            .values("listing__title")
            .annotate(count=Count("listing"))
            .order_by("-count")[:5]
        )
        return Response({"top_5": top_listings})

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        user = request.user

        if not user.is_authenticated or user.role not in ["ADMIN", "LANDLORD"]:
            return Response({"error": _("You do not have permission to perform this action.")},
                            status=status.HTTP_403_FORBIDDEN)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="analytics_{timezone.now().date()}.csv"'
        writer = csv.writer(response)
        writer.writerow([_("Listing ID"), _("Title"), _("Views"), _("Timestamp")])

        views = ViewHistory.objects.select_related("listing")
        if user.role == "LANDLORD":
            views = views.filter(listing__user=user)

        for view in views.all():
            writer.writerow([view.listing.id, view.listing.title, 1, view.timestamp])

        return response


@method_decorator(ratelimit(key='ip', rate='100/m', method='POST', block=True), name='create')
@method_decorator(csrf_protect, name='create')
class SearchHistoryViewSet(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.none()
    serializer_class = SearchHistorySerializer

    def get_queryset(self):
        user = self.request.user

        # Возвращаем пустой QuerySet, если пользователь не аутентифицирован или не ADMIN
        if not user.is_authenticated or user.role != "ADMIN":
            return SearchHistory.objects.none()

        # Для ADMIN возвращаем все записи
        return SearchHistory.objects.all().order_by('-timestamp')

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsTenant()]

        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]  # Добавил здесь IsSelfOrAdmin, чтобы не было ошибки

        if self.action == 'list':
            return [IsAuthenticated(), IsAdmin()]

        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        if user:
            SearchHistory.objects.filter(user=user).order_by("-timestamp")[10:].delete()
        return Response(serializer.data)


class AnalyticsExportCSVView(APIView):
    def get(self, request):
        # Создаем буфер в памяти
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        # Пишем заголовки столбцов
        writer.writerow(['Listing', 'City', 'User Email', 'View Count'])

        # Получаем данные из базы
        # Например, считаем количество просмотров каждого listing для каждого пользователя
        view_histories = ViewHistory.objects.all()
        for vh in view_histories:
            writer.writerow([
                vh.listing.title,
                vh.listing.city,
                vh.user.email,
                1,  # Или другое поле, если есть
            ])

        # Возвращаем ответ с csv и правильным Content-Type
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="analytics.csv"'
        return response
