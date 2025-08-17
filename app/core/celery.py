import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Refresh schedule from env
    minutes = int(os.environ.get("REFRESH_MINUTES", "60"))
    sender.add_periodic_task(
        minutes * 60,
        name="refresh_playlists_and_snapshot",
        sig=app.signature("tubarr.tasks.refresh_all_and_snapshot"),
    )
