### `users/tasks.py`

import secrets
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from sentry_sdk import capture_exception

from .models import User, VerificationToken


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        activate(user.language)
        token = secrets.token_urlsafe(32)
        VerificationToken.objects.create(
            user=user, token=token, expires_at=timezone.now() + timedelta(hours=24)
        )
        subject = _("Verify Your MietSystem Account")
        message = _(f"Click to verify: {settings.FRONTEND_URL}/verify-email/{token}/")
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except User.DoesNotExist:
        capture_exception()
        raise self.retry(countdown=60)
    except Exception as e:
        capture_exception(e)
        raise self.retry(countdown=60)


@shared_task(bind=True, max_retries=3)
def send_reset_password_email(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        activate(user.language)
        token = secrets.token_urlsafe(32)
        VerificationToken.objects.create(
            user=user, token=token, expires_at=timezone.now() + timedelta(hours=24)
        )
        subject = _("Reset Your MietSystem Password")
        message = _(f"Click to reset: {settings.FRONTEND_URL}/reset-password/{token}/")
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except User.DoesNotExist:
        capture_exception()
        raise self.retry(countdown=60)
    except Exception as e:
        capture_exception(e)
        raise self.retry(countdown=60)


@shared_task
def cleanup_expired_tokens():
    VerificationToken.objects.filter(expires_at__lt=timezone.now()).delete()


# from celery import shared_task
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import User
#
# @shared_task
# def send_verification_email(user_id):
#     user = User.objects.get(id=user_id)
#     subject = 'Verify Your MietSystem Account'
#     message = f'Click to verify: {settings.FRONTEND_URL}/verify-email/{user.id}/'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
#
# @shared_task
# def send_reset_password_email(user_id):
#     user = User.objects.get(id=user_id)
#     subject = 'Reset Your MietSystem Password'
#     message = f'Click to reset: {settings.FRONTEND_URL}/reset-password/{user.id}/'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
