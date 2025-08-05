# core/router.py
from rest_framework.routers import DefaultRouter

from bookings.views import BookingViewSet
from listings.views import ListingViewSet
from locations.views import LocationViewSet
from reviews.views import ReviewViewSet
from users.views import UserViewSet
from analytics.views import AnalyticsViewSet, SearchHistoryViewSet

# Создаем единственный главный роутер для всего проекта
router = DefaultRouter()

# Регистрируем все ViewSet'ы в одном месте
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"users", UserViewSet, basename="user")
# Правильные префиксы роутов для Analytics
router.register(r"analytics-views", AnalyticsViewSet, basename="analytics-views")
router.register(r"analytics-searches", SearchHistoryViewSet, basename="analytics-searches")
