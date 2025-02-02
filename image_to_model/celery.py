import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_to_model.settings')

app = Celery('image_to_model')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')