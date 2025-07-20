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
from analytics.models import ViewHistory
from django.conf import settings
import sentry_sdk
from redis import Redis
from core.celery import app as celery_app
from botocore.exceptions import ClientError
from decouple import config
import boto3

try:
    from slack_sdk import WebClient
except ImportError:
    WebClient = None

class HealthCheckService:
    def __init__(self):
        self.redis_client = Redis.from_url(settings.CACHES['default']['LOCATION'])
        self.s3_client = boto3.client('s3')
        self.s3_bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.slack_client = WebClient(token=config('SLACK_TOKEN', default='')) if WebClient and config('SLACK_TOKEN', default='') else None

    def run_all_checks(self, user=None):
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
                "listings": Listing.objects.filter(user=user).count() if user and user.role == "LANDLORD" else Listing.objects.count(),
                "bookings": Booking.objects.filter(user=user).count() if user and user.role == "TENANT" else Booking.objects.count(),
                "reviews": Review.objects.count(),
                "locations": Location.objects.count(),
                "views": ViewHistory.objects.filter(user=user).count() if user and user.role == "TENANT" else ViewHistory.objects.count(),
            },
            "system_metrics": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_free_gb": round(psutil.disk_usage('/').free / (1024 ** 3), 2),
                "celery_tasks": PeriodicTask.objects.count(),
            },
        }
        # [Изменение] Добавлен параметр user для фильтрации stats по текущему пользователю
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
            start = now()
            cache.set("healthcheck_test", "ok", timeout=5)
            info = self.redis_client.info()
            keys = info['db0']['keys'] if 'db0' in info else 0
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
            latency = (now() - start).total_seconds() * 1000
            status = "online" if latency < 100 else "warning"
            return {
                "status": status,
                "latency_ms": round(latency, 2),
                "keys": keys,
                "hit_rate": round(hit_rate, 2)
            }
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def check_celery(self):
        try:
            inspect = celery_app.control.inspect()

            stats = inspect.stats()
            active_tasks_raw = inspect.active() or {}
            scheduled_tasks_raw = inspect.scheduled() or {}

            active_tasks = sum(len(tasks) for tasks in active_tasks_raw.values()) if active_tasks_raw else 0
            scheduled_tasks = sum(len(tasks) for tasks in scheduled_tasks_raw.values()) if scheduled_tasks_raw else 0

            return {
                "status": "online" if stats else "offline",
                "active_tasks": active_tasks,
                "queued_tasks": scheduled_tasks
            }

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
