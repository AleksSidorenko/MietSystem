### `core/urls.py`

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

# ViewSets
from bookings.views import BookingViewSet
from core.views import status_page_view
from listings.views import ListingViewSet
from locations.views import LocationViewSet
from reviews.views import ReviewViewSet

# from core.views import healthcheck_view  # 👈 Добавили






router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path("", status_page_view, name="status"),
    # path('', healthcheck_view),  # 👈 Живая сводка вместо редиректа
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/users/", include("users.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# from django.contrib import admin
# from django.urls import path, include
# from drf_spectacular.views import (
#     SpectacularAPIView,
#     SpectacularRedocView,
#     SpectacularSwaggerView,
# )
# from rest_framework.routers import DefaultRouter
# from bookings.views import BookingViewSet
# from core.views import healthcheck_view
#
#
#
# # Импортируйте другие ViewSets, если они у вас есть и зарегистрированы в этом роутере
# # from listings.views import ListingViewSet
# # from users.views import UserViewSet
# # from reviews.views import ReviewViewSet
# # ... и так далее для других ViewSets, которые вы хотите добавить в этот же роутер
#
# router = DefaultRouter()
# router.register(r'bookings', BookingViewSet, basename='booking')
# # router.register(r'listings', ListingViewSet, basename='listing') # Пример, если вы хотите включить ListingViewSet сюда
# # router.register(r'users', UserViewSet, basename='user') # Пример
# # router.register(r'reviews', ReviewViewSet, basename='review') # Пример
#
#
# urlpatterns = [
#     path('', healthcheck_view),  # 👈 наша HTML-страница
#     path('admin/', admin.site.urls),
#     # Если вы используете отдельные router'ы или ViewSets для этих приложений,
#     # то эти строки будут ссылаться на их собственные urls.py
#     path('api/users/', include('users.urls')),
#     path('api/listings/', include('listings.urls')),
#     # path('api/bookings/', include('bookings.urls')),  # <-- УДАЛИТЬ ИЛИ ЗАКОММЕНТИРОВАТЬ ЭТУ СТРОКУ
#     path('api/reviews/', include('reviews.urls')),
#     path('api/analytics/', include('analytics.urls')),
#     path('api/locations/', include('locations.urls')),
#
#     # Включите маршруты, сгенерированные DefaultRouter
#     path('api/', include(router.urls)),  # <-- РАСКОММЕНТИРОВАТЬ ЭТУ СТРОКУ
#
#     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
#     path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
#     path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
# ]
