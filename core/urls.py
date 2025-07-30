# core/urls.py
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from core.authentication import (
    CookieJWTAuthenticationScheme,
    OpenApiAuthenticationExtension,
)
from core.router import router  # <-- Импорт router из router.py (единственный)
from core.views import (
    HealthCheckAPIView,
    configure_s3,
    login_view,
    logout_page_view,
    logout_view,
    restart_celery,
    status_page_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/users/", include("users.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/health/", HealthCheckAPIView.as_view(), name="api-healthcheck"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("configure-s3/", configure_s3, name="configure_s3"),
    path("restart-celery/", restart_celery, name="restart_celery"),
    path(
        "logout/action/", logout_view, name="logout"
    ),  # [Изменено] Путь для logout_view
    path(
        "logout/", logout_page_view, name="logout_page"
    ),  # [Добавлено] Путь для страницы выхода
    path(
        "login/", login_view, name="login"
    ),  # [Добавлено] Маршрут для кастомного логина
]

urlpatterns += i18n_patterns(
    path("", status_page_view, name="status"),
    prefix_default_language=False,
)

# if settings.DEBUG:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
