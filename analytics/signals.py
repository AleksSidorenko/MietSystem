### `analytics/signals.py`

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_message

from .models import SearchHistory, ViewHistory


@receiver(post_save, sender=SearchHistory)
def log_search_history(sender, instance, created, **kwargs):
    if created:
        user_email = instance.user.email if instance.user else "Anonymous"
        message = str(
            _(f"Search query '{instance.query}' by {user_email} at {timezone.now()}")
        )
        capture_message(message, level="info")


@receiver(post_save, sender=ViewHistory)
def log_view_history(sender, instance, created, **kwargs):
    if created:
        user_email = instance.user.email if instance.user else "Anonymous"
        message = str(
            _(
                f"View of listing '{instance.listing.title}' by {user_email} at {timezone.now()}"
            )
        )
        capture_message(message, level="info")
