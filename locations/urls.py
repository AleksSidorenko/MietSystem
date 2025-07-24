# locations/urls.py

from rest_framework.routers import DefaultRouter

from .views import LocationViewSet

router = DefaultRouter()
router.register("", LocationViewSet)
urlpatterns = router.urls
