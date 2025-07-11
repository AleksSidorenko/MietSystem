### `analytics/urls.py`

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnalyticsViewSet, SearchHistoryViewSet

router = DefaultRouter()
router.register("views", AnalyticsViewSet, basename="analytics")
router.register("searches", SearchHistoryViewSet, basename="searches")

urlpatterns = [
    path("", include(router.urls)),
]
