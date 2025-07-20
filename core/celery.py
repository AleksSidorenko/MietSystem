# core/celery.py

from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from decouple import config

# Установите переменную окружения для настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Создайте экземпляр приложения Celery
app = Celery("mietsystem")

# Загрузите настройки из настроек Django с пространством имен CELERY
app.config_from_object("django.conf:settings", namespace="CELERY")

# Настройка Celery с использованием decouple
app.conf.broker_url = config("CELERY_BROKER_URL")
app.conf.result_backend = config("REDIS_URL")

# Автоматически обнаруживайте и регистрируйте задачи из всех приложений Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
