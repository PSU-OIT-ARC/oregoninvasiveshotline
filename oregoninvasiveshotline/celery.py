import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'oregoninvasiveshotline.settings')
from django.conf import settings

app = Celery('oregoninvasiveshotline')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
