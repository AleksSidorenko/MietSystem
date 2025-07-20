# core/router.py
from rest_framework.routers import DefaultRouter
from bookings.views import BookingViewSet
from listings.views import ListingViewSet
from locations.views import LocationViewSet
from reviews.views import ReviewViewSet

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"reviews", ReviewViewSet, basename="review")
