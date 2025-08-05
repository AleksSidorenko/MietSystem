# core/tasks.py
from celery import shared_task
from django.utils.timezone import now
from django.core.cache import cache
from redis import Redis
from django.conf import settings
from datetime import datetime, timezone, timedelta

@shared_task
def save_hit_rate():
    redis_client = Redis.from_url(settings.CACHES['default']['LOCATION'])
    try:
        info = redis_client.info()
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
        key = f'hit_rate_{datetime.now(timezone.utc).strftime("%Y%m%d%H")}'
        redis_client.setex(key, 24 * 3600, hit_rate)
        print(f"Saved hit_rate: {hit_rate} for key {key}")
    except Exception as e:
        print(f"Failed to save hit_rate: {str(e)}")