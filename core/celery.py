# core/celery.py
import os
from celery import Celery
from decouple import config
# Явный импорт задачи для надежности
from core.tasks import save_hit_rate

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('mietsystem')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_url = config('CELERY_BROKER_URL')
app.conf.result_backend = config('REDIS_URL')

# Автоматически находить задачи в приложениях из INSTALLED_APPS
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
