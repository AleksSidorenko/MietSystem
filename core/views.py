# core/views.py
from django.conf import settings
from django.utils.timezone import now
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.views.decorators.cache import cache_page
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.health import HealthCheckService

class HealthCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = HealthCheckService()
        data = service.run_all_checks()
        return Response(data)

# @cache_page(60)  # Кэширование на 60 секунд
def status_page_view(request):
    if not settings.DEBUG and not request.user.is_authenticated:
        return HttpResponseForbidden("Доступ запрещен. Пожалуйста, войдите.")

    service = HealthCheckService()
    data = service.run_all_checks()

    context = {
        "data": data,
        "show_debug": settings.DEBUG,
        "time_now": now(),
    }
    return render(request, "core/status_page.html", context)