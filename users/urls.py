### `users/urls.py`

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import CustomTokenObtainPairView, UserViewSet

router = DefaultRouter()
router.register("", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]


# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )
# from .views import UserViewSet
#
# router = DefaultRouter()
# router.register('', UserViewSet)
#
# urlpatterns = [
#     path('', include(router.urls)),
#     path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
# ]
