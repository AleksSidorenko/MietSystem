### `reviews/signals.py`

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_message

from .models import Review


@receiver(post_save, sender=Review)
def log_review_activity(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    message = str(
        _(
            f"Review {instance.id} {action} at {timezone.now()} by user {instance.user.email}"
        )
    )
    capture_message(message, level="info")


@receiver(post_save, sender=Review)
def update_listing_rating(sender, instance, **kwargs):
    if instance.is_approved:
        from analytics.tasks import update_average_rating

        update_average_rating.delay(instance.booking.listing.id)
