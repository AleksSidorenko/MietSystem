# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from bookings.views import BookingViewSet
from core.views import status_page_view, HealthCheckAPIView
from listings.views import ListingViewSet
from locations.views import LocationViewSet
from reviews.views import ReviewViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/users/", include("users.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/health/", HealthCheckAPIView.as_view(), name="api-healthcheck"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("", status_page_view, name="status"),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# # `core/urls.py`
#
# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.conf.urls.i18n import i18n_patterns
# from django.urls import include, path
# from drf_spectacular.views import (
#     SpectacularAPIView,
#     SpectacularRedocView,
#     SpectacularSwaggerView,
# )
# from rest_framework.routers import DefaultRouter
# from bookings.views import BookingViewSet
# from core.views import status_page_view, HealthCheckAPIView
# from listings.views import ListingViewSet
# from locations.views import LocationViewSet
# from reviews.views import ReviewViewSet
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
#     TokenVerifyView,
# )
#
# router = DefaultRouter()
# router.register(r"bookings", BookingViewSet, basename="booking")
# router.register(r"listings", ListingViewSet, basename="listing")
# router.register(r"locations", LocationViewSet, basename="location")
# router.register(r"reviews", ReviewViewSet, basename="review")
#
# urlpatterns = [
#     path("", status_page_view, name="status"),
#     path("admin/", admin.site.urls),
#     path("api/", include(router.urls)),
#     path("api/users/", include("users.urls")),
#     path("api/analytics/", include("analytics.urls")),
#     path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
#     path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
#     path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
#     path("api/health/", HealthCheckAPIView.as_view(), name="api-healthcheck"),
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
#     path("i18n/", include("django.conf.urls.i18n")),  # Для переключения языка
#     # path("api/token/", include("rest_framework_simplejwt.urls")),  # JWT endpoints
# ]
#
# # Локализованные URL для главной страницы
# # urlpatterns += i18n_patterns(
# #     path("", status_page_view, name="status"),
# # )
# urlpatterns += i18n_patterns(
#     path("", status_page_view, name="status"),
#     prefix_default_language=False,  # Убирает префикс для языка по умолчанию
# )
#
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
