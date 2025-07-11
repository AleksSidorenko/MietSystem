### listings/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_message

from .models import Listing


@receiver(post_save, sender=Listing)
def log_listing_activity(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    message = str(
        _(
            f"Listing {instance.title} {action} at {timezone.now()} by user {instance.user.email}"
        )
    )
    capture_message(message, level="info")
