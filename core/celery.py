# core/celery.py
import os
from celery import Celery
from decouple import config

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('mietsystem')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_url = config('CELERY_BROKER_URL')
app.conf.result_backend = config('REDIS_URL')

# Автоматически находить задачи в приложениях из INSTALLED_APPS
app.autodiscover_tasks()

# Явный импорт задачи для надежности
from core.tasks import save_hit_rate

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# from __future__ import absolute_import, unicode_literals
# import os
# from celery import Celery
# from decouple import config
#
# # Установите переменную окружения для настроек Django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
#
# # core/celery.py
# app = Celery("core")
#
# # Загрузите настройки из настроек Django с пространством имен CELERY
# app.config_from_object("django.conf:settings", namespace="CELERY")
#
# # Настройка Celery с использованием decouple
# app.conf.broker_url = config("CELERY_BROKER_URL")
# app.conf.result_backend = config("REDIS_URL")
#
# # Автоматически обнаруживайте и регистрируйте задачи из всех приложений Django
# app.autodiscover_tasks()
#
#
# @app.task(bind=True)
# def debug_task(self):
#     print(f"Request: {self.request!r}")
#
