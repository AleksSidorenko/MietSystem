# core/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.health import HealthCheckService
from django.urls import get_resolver
import logging
import os
import subprocess

try:
    from axes.models import AccessAttempt
except ImportError:
    AccessAttempt = None

from decouple import config
from django.urls import reverse
from rest_framework import generics, serializers
from core.router import router # Импортируем главный роутер
from users.views import AllUsersForAdminDashboardView # Добавлен импорт


# Настройка логирования
logger = logging.getLogger(__name__)

class EmptySerializer(serializers.Serializer):
    pass

class HealthCheckAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    def get(self, request):
        return Response({"status": "ok"})

@login_required
def status_page_view(request):
    logger.info(
        f"User: {request.user}, Authenticated: {request.user.is_authenticated}, Role: {getattr(request.user, 'role', 'None')}"
    )
    if not request.user.is_authenticated:
        login_url = getattr(settings, "LOGIN_URL", "/admin/login/")
        logger.info(f"Redirecting to: {login_url}?next={request.path}")
        return redirect(f"{login_url}?next={request.path}")

    service = HealthCheckService()
    data = service.run_all_checks(user=request.user)
    logger.debug(f"HealthCheckService data: {data}")

    # Валидация данных
    if 'database' not in data:
        data['database'] = {'status': 'unknown', 'error': 'Database status not provided'}
    if 'redis' not in data:
        data['redis'] = {'status': 'unknown', 'error': 'Redis status not provided', 'keys': 0, 'used_memory_human': 'N/A', 'hit_rate': 0, 'hit_rate_history': [], 'latency_ms': 0}
    if 'system_metrics' not in data:
        data['system_metrics'] = {
            'cpu_percent': 0, 'memory_percent': 0, 'disk_free_gb': 0,
            'cpu_max_threshold': 80, 'memory_max_threshold': 90, 'disk_min_threshold': 10
        }
    if 'users' not in data:
        data['users'] = {'total': 0, 'admins': 0, 'landlords': 0, 'tenants': 0}
    if 'stats' not in data:
        data['stats'] = {'listings': 0, 'bookings': 0, 'reviews': 0, 'locations': 0}

    data["last_updated"] = now().strftime("%Y-%m-%d %H:%M:%S")
    data["login_attempts"] = (
        AccessAttempt.objects.all().order_by("-attempt_time")[:5]
        if AccessAttempt
        else []
    )

    # Подсчёт эндпоинтов (исправленная логика)
    try:
        endpoints_total = 0
        endpoints_get = 0
        endpoints_post = 0
        endpoints_put = 0
        endpoints_delete = 0

        # Считаем эндпоинты из главного роутера DRF
        for prefix, viewset, basename in router.registry:
            viewset_instance = viewset()
            methods = [m.lower() for m in viewset_instance.http_method_names if m.lower() in ['get', 'post', 'put', 'delete']]

            # Роутер создает два URL для каждого ViewSet: список и детали
            endpoints_total += 2
            endpoints_get += 1 if 'get' in methods else 0
            endpoints_get += 1 if 'retrieve' in methods else 0 # Детальный GET
            endpoints_post += 1 if 'post' in methods else 0
            endpoints_put += 1 if 'put' in methods else 0
            endpoints_delete += 1 if 'delete' in methods else 0

        # Добавляем вручную прописанные эндпоинты из core/urls.py
        # Определяем методы для каждого
        endpoints_total += 1 # /api/schema/
        endpoints_get += 1
        endpoints_total += 1 # /api/docs/
        endpoints_get += 1
        endpoints_total += 1 # /api/swagger/
        endpoints_get += 1
        endpoints_total += 1 # /api/redoc/
        endpoints_get += 1
        endpoints_total += 1 # /api/health/
        endpoints_get += 1
        endpoints_total += 1 # /api/token/
        endpoints_post += 1
        endpoints_total += 1 # /api/token/refresh/
        endpoints_post += 1
        endpoints_total += 1 # /api/token/verify/
        endpoints_post += 1
        endpoints_total += 1 # /api/users/all_users_for_admin_dashboard/
        endpoints_get += 1

        data["endpoints_total"] = endpoints_total
        data["endpoints_get"] = endpoints_get
        data["endpoints_post"] = endpoints_post
        data["endpoints_put"] = endpoints_put
        data["endpoints_delete"] = endpoints_delete

    except Exception as e:
        logger.error(f"Error counting endpoints: {e}")
        data["endpoints_total"] = 0
        data["endpoints_get"] = 0
        data["endpoints_post"] = 0
        data["endpoints_put"] = 0
        data["endpoints_delete"] = 0

    user_avatar_url = None
    if hasattr(request.user, 'avatar') and request.user.avatar:
        user_avatar_url = request.user.avatar.url

    context = {
        "data": data,
        "show_debug": settings.DEBUG,
        "time_now": now(),
        "user_email": request.user.email if request.user.is_authenticated else "",
        "user_role": (
            getattr(request.user, "role", "None")
            if request.user.is_authenticated
            else "None"
        ),
        "user_role_display": (
            request.user.get_role_display()
            if request.user.is_authenticated
               and hasattr(request.user, "get_role_display")
            else "None"
        ),
        "user_first_name": (
            request.user.first_name
            if request.user.is_authenticated and hasattr(request.user, "first_name")
            else ""
        ),
        "user_last_name": (
            request.user.last_name
            if request.user.is_authenticated and hasattr(request.user, "last_name")
            else ""
        ),
        "user_avatar_url": user_avatar_url,
    }
    return render(request, "core/status_page.html", context)

def logout_view(request):
    logger.info(f"Logging out user: {request.user}")
    logout(request)
    request.session.flush()
    return redirect("logout_page")

def logout_page_view(request):
    return render(request, "core/logout.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("status")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info(f"User {user.email} logged in, redirecting to /")
                return redirect("status")
            else:
                messages.error(request, "Неверный email или пароль.")
        else:
            messages.error(request, "Неверный email или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, "core/login.html", {"form": form})

def configure_s3(request):
    if request.method == "POST":
        bucket_name = request.POST.get("bucket_name")
        aws_access_key_id = request.POST.get("aws_access_key_id")
        aws_secret_access_key = request.POST.get("aws_secret_access_key")
        if bucket_name and aws_access_key_id and aws_secret_access_key:
            try:
                env_path = os.path.join(settings.BASE_DIR, ".env")
                with open(env_path, "a") as f:
                    f.write(f"\nAWS_STORAGE_BUCKET_NAME={bucket_name}\n")
                    f.write(f"AWS_ACCESS_KEY_ID={aws_access_key_id}\n")
                    f.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")
                messages.success(request, "S3 настроен успешно.")
            except Exception as e:
                messages.error(request, f"Ошибка настройки S3: {str(e)}")
        else:
            messages.error(request, "Все поля должны быть заполнены.")
        return HttpResponseRedirect("/dashboard/")
    return render(request, "core/configure_s3.html", {})

def restart_celery(request):
    try:
        if os.name == "posix" and "darwin" in os.uname().sysname.lower():
            subprocess.run(["pkill", "-f", "celery"], check=True)
            subprocess.run(
                ["celery", "-A", "core", "worker", "--loglevel=info", "&"], check=True
            )
        else:
            subprocess.run(["systemctl", "restart", "celery"], check=True)
        messages.success(request, "Celery перезапущен.")
    except subprocess.CalledProcessError as e:
        messages.error(f"Ошибка при перезапуске Celery: {str(e)}")
    return HttpResponseRedirect("/dashboard/")
