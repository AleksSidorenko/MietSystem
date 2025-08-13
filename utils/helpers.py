# utils/helpers.py
from datetime import datetime
from django.core.cache import cache
from django.utils import timezone


def calculate_popularity(views, reviews, created_at):
    time_decay = (timezone.now() - created_at).days
    score = (views * 0.5 + reviews * 2) / (1 + time_decay / 30)
    return round(score, 2)


def cache_popularity(listing_id, score):
    cache_key = f"popularity_{listing_id}"
    cache.set(cache_key, score, timeout=3600)
