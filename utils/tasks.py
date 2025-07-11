#### `utils/tasks.py`

from celery import shared_task
from django.core.cache import cache

from listings.models import Listing

from .helpers import cache_popularity, calculate_popularity


@shared_task
def update_popularity():
    listings = Listing.objects.filter(is_active=True)
    for listing in listings:
        views = listing.viewhistory_set.count()
        reviews = listing.reviews.filter(is_approved=True).count()
        popularity = calculate_popularity(views, reviews, listing.created_at)
        cache_popularity(listing.id, popularity)
