import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("yavar")

# All Celery configuration lives in Django settings under the CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py modules in installed Django apps.
app.autodiscover_tasks()
