# core/views.py

from django.conf import settings
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.health import HealthCheckService
try:
    from axes.models import AccessAttempt
except ImportError:
    AccessAttempt = None
from core.router import router
import subprocess
import os
from decouple import config, Config, RepositoryEnv
from rest_framework import generics, serializers

class EmptySerializer(serializers.Serializer):
    pass

class HealthCheckAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    def get(self, request):
        # логика проверки здоровья, например
        return Response({"status": "ok"})

    # def get(self, request):
    #     service = HealthCheckService()
    #     data = service.run_all_checks(user=request.user)
    #     return Response(data)

def status_page_view(request):
    print(f"User: {request.user}, Authenticated: {request.user.is_authenticated}, Role: {getattr(request.user, 'role', 'None')}")  # Отладочный вывод
    if not request.user.is_authenticated:
        login_url = getattr(settings, 'LOGIN_URL', '/admin/login/')
        print(f"Redirecting to: {login_url}?next={request.path}")  # Отладочный вывод
        return redirect(f"{login_url}?next={request.path}")

    service = HealthCheckService()
    data = service.run_all_checks(user=request.user)
    data['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
    data['login_attempts'] = AccessAttempt.objects.all().order_by('-attempt_time')[:5] if AccessAttempt else []
    try:
        data['endpoints'] = len([url for url in router.registry])
    except AttributeError:
        data['endpoints'] = 0

    context = {
        'data': data,
        'show_debug': settings.DEBUG,
        'time_now': now(),
        'user_email': request.user.email if request.user.is_authenticated else '',
        'user_role': getattr(request.user, 'role', 'None') if request.user.is_authenticated else 'None',
        'user_role_display': request.user.get_role_display() if request.user.is_authenticated and hasattr(request.user, 'get_role_display') else 'None',
        'user_first_name': request.user.first_name if request.user.is_authenticated and hasattr(request.user, 'first_name') else '',
        'user_last_name': request.user.last_name if request.user.is_authenticated and hasattr(request.user, 'last_name') else '',
    }
    return render(request, "core/status_page.html", context)

def logout_view(request):
    print(f"Logging out user: {request.user}")  # Отладочный вывод
    logout(request)  # Очищает авторизацию
    request.session.flush()  # Полностью очищает сессию
    return redirect('logout_page')

def logout_page_view(request):
    return render(request, "core/logout.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect('status')  # Если пользователь уже авторизован, перенаправляем на дашборд
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print(f"User {user.email} logged in, redirecting to /")  # Отладочный вывод
                return redirect('status')  # Перенаправление на дашборд
            else:
                messages.error(request, "Неверный email или пароль.")
        else:
            messages.error(request, "Неверный email или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, "core/login.html", {'form': form})

def configure_s3(request):
    if request.method == 'POST':
        bucket_name = request.POST.get('bucket_name')
        aws_access_key_id = request.POST.get('aws_access_key_id')
        aws_secret_access_key = request.POST.get('aws_secret_access_key')
        if bucket_name and aws_access_key_id and aws_secret_access_key:
            try:
                env_path = os.path.join(settings.BASE_DIR, '.env')
                with open(env_path, 'a') as f:
                    f.write(f"\nAWS_STORAGE_BUCKET_NAME={bucket_name}\n")
                    f.write(f"AWS_ACCESS_KEY_ID={aws_access_key_id}\n")
                    f.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")
                messages.success(request, 'S3 настроен успешно.')
            except Exception as e:
                messages.error(request, f'Ошибка настройки S3: {str(e)}')
        else:
            messages.error(request, 'Все поля должны быть заполнены.')
        return HttpResponseRedirect('/dashboard/')
    return render(request, 'core/configure_s3.html', {})

def restart_celery(request):
    try:
        if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
            subprocess.run(['pkill', '-f', 'celery'], check=True)
            subprocess.run(['celery', '-A', 'core', 'worker', '--loglevel=info', '&'], check=True)
        else:
            subprocess.run(['systemctl', 'restart', 'celery'], check=True)
        messages.success(request, 'Celery перезапущен.')
    except subprocess.CalledProcessError as e:
        messages.error(request, f'Ошибка при перезапуске Celery: {str(e)}')
    return HttpResponseRedirect('/dashboard/')
