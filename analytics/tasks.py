# analytics/tasks.py
from datetime import timedelta, timezone

from celery import shared_task
from django.db.models import Avg

from analytics.models import ViewHistory
from listings.models import Listing
from reviews.models import Review


@shared_task
def update_average_rating(listing_id):
    listing = Listing.objects.get(id=listing_id)
    reviews = Review.objects.filter(booking__listing=listing, is_approved=True)
    if reviews.exists():
        avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
        listing.average_rating = round(avg_rating, 1)
        listing.save()


@shared_task
def cleanup_old_views():
    threshold = timezone.now() - timedelta(days=90)
    ViewHistory.objects.filter(timestamp__lt=threshold).delete()
