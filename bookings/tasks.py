### `bookings/tasks.py`
from datetime import timedelta, timezone

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception

from .models import Booking


@shared_task(bind=True, max_retries=3)
def send_booking_notification(self, booking_id, action):
    try:
        booking = Booking.objects.get(id=booking_id)
        activate(booking.user.language)
        subject = str(_(f"Booking {action} - {booking.listing.title}"))
        message = str(
            _(f"Your booking for {booking.listing.title} has been {action.lower()}.\n")
        )
        message += str(_(f"Dates: {booking.start_date} to {booking.end_date}\n"))
        message += str(_(f"Total Price: {booking.total_price} EUR"))
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            fail_silently=False,
        )
    except Booking.DoesNotExist:
        capture_exception()
        raise self.retry(countdown=60)
    except Exception as e:
        capture_exception(e)
        raise self.retry(countdown=60)


@shared_task
def cleanup_old_bookings():
    threshold = timezone.now().date() - timedelta(days=30)
    Booking.objects.filter(status="PENDING", created_at__lt=threshold).delete()
