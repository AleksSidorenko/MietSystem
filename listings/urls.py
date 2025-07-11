### `listings/urls.py`

from rest_framework.routers import DefaultRouter

from .views import ListingViewSet

router = DefaultRouter()
router.register("", ListingViewSet)
urlpatterns = router.urls


# from rest_framework.routers import DefaultRouter
# from .views import ListingViewSet
#
# router = DefaultRouter()
# router.register('', ListingViewSet)
# urlpatterns = router.urls
