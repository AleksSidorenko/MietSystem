# bookings/tasks.py
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception
from .models import Booking
from django.db import connection


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




@shared_task
def update_completed_bookings():
    """
    Проверяет и обновляет статус бронирований,
    чей срок аренды уже закончился.
    """
    now_date = timezone.now().date()

    bookings_to_update = Booking.objects.filter(
        status__in=["CONFIRMED", "PENDING"],
        end_date__lt=now_date
    )

    print("Executing query:")
    print(bookings_to_update.query)

    updated_count = bookings_to_update.update(status="COMPLETED")
    print(f"Updated {updated_count} bookings to COMPLETED status.")