### reviews/tasks.py

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _

from .models import Review


@shared_task
def send_review_notification(review_id):
    review = Review.objects.get(id=review_id)
    activate(review.user.language)
    subject = str(_(f"New review for {review.booking.listing.title}"))
    message = str(
        _(
            f"Your review with rating {review.rating} has been submitted and awaits approval."
        )
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[review.user.email],
        fail_silently=False,
    )
