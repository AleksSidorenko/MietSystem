### listings/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_message
from datetime import date, timedelta

from .models import Listing, AvailabilitySlot


@receiver(post_save, sender=Listing)
def log_listing_activity(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    message = str(
        _(
            f"Listing {instance.title} {action} at {timezone.now()} by user {instance.user.email}"
        )
    )
    capture_message(message, level="info")


@receiver(post_save, sender=Listing)
def create_default_availability(sender, instance, created, **kwargs):
    """Создает 10 дней доступности после создания нового объявления"""
    if created:
        today = date.today()
        for i in range(5):
            date_obj = today + timedelta(days=i)
            AvailabilitySlot.objects.get_or_create(
                listing=instance,
                date=date_obj,
                defaults={'is_available': True}
            )
