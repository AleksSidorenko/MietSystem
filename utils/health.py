# utils/health.py

import os
import psutil
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db import connection
from django.core.cache import cache
from django_celery_beat.models import PeriodicTask
from bookings.models import Booking
from listings.models import Listing
from reviews.models import Review
from locations.models import Location
from django.conf import settings
import sentry_sdk
from redis import Redis
from celery import current_app as celery_app
import boto3
from botocore.exceptions import ClientError
from decouple import config

try:
    from slack_sdk import WebClient
except ImportError:
    WebClient = None  # Graceful degradation if slack-sdk not installed

class HealthCheckService:
    def __init__(self):
        self.redis_client = Redis.from_url(settings.CACHES['default']['LOCATION'])
        self.s3_client = boto3.client('s3')
        self.s3_bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.slack_client = WebClient(token=config('SLACK_TOKEN', default='')) if WebClient and config('SLACK_TOKEN', default='') else None

    def run_all_checks(self):
        User = get_user_model()
        data = {
            "time": now(),
            "database": self.check_database(),
            "redis": self.check_redis(),
            "celery": self.check_celery(),
            "s3": self.check_s3(),
            "localization": self.check_localization(),
            "users": {
                "total": User.objects.count(),
                "admins": User.objects.filter(role="ADMIN").count(),
                "landlords": User.objects.filter(role="LANDLORD").count(),
                "tenants": User.objects.filter(role="TENANT").count(),
            },
            "stats": {
                "listings": Listing.objects.count(),
                "bookings": Booking.objects.count(),
                "reviews": Review.objects.count(),
                "locations": Location.objects.count(),
            },
            "system_metrics": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_free_gb": round(psutil.disk_usage('/').free / (1024 ** 3), 2),
                "celery_tasks": PeriodicTask.objects.count(),
            },
        }
        # Уведомления при сбоях
        failed_services = [
            key for key, value in data.items()
            if key in ['database', 'redis', 'celery', 's3', 'localization'] and value['status'] == 'offline'
        ]
        if failed_services:
            self.notify_sentry(failed_services)
            self.notify_slack(failed_services)
        return data

    def check_database(self):
        try:
            connection.ensure_connection()
            return {"status": "online"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def check_redis(self):
        try:
            cache.set("healthcheck_test", "ok", timeout=5)
            return {"status": "online"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def check_celery(self):
        try:
            stats = celery_app.control.inspect().stats()
            return {"status": "online" if stats else "offline"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def check_s3(self):
        if not self.s3_bucket:
            return {"status": "offline", "error": "S3 bucket name not configured."}
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            return {"status": "online"}
        except ClientError as e:
            return {"status": "offline", "error": str(e)}

    def check_localization(self):
        try:
            langs = [lang[0] for lang in settings.LANGUAGES]
            return {"status": "online", "languages": langs}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def notify_sentry(self, failed_services):
        if settings.SENTRY_DSN:
            sentry_sdk.capture_message(f"Health check failed for services: {', '.join(failed_services)}")

    def notify_slack(self, failed_services):
        if self.slack_client and failed_services:
            try:
                self.slack_client.chat_postMessage(
                    channel='#monitoring',
                    text=f"🚨 Health check failed for: {', '.join(failed_services)}"
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)