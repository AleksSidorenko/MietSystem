# users/signals.py

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_message

from users.models import User


@receiver(post_save, sender=User)
def sync_user_role_and_group(sender, instance, created, **kwargs):
    # Skip for superuser
    if instance.is_superuser:
        return

    # 1. Logging
    action = "created" if created else "updated"
    capture_message(f"User {instance.email} {action} at {timezone.now()}", level="info")

    # 2. Sync group
    instance.groups.clear()
    try:
        group_name = instance.role.capitalize()  # 'TENANT' -> 'Tenant'
        group = Group.objects.get(name=group_name)
        instance.groups.add(group)

        # 3. Ensure is_staff for admin panel access
        if not instance.is_staff:
            instance.is_staff = True
            instance.save(update_fields=["is_staff"])

    except Group.DoesNotExist:
        capture_message(
            f"[SYNC] Group '{group_name}' not found for user {instance.email}",
            level="warning",
        )
    except Exception as e:
        capture_message(f"[SYNC ERROR] {e} for user {instance.email}", level="error")
