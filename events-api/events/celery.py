import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "events_api.settings")

REDIS_URL = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery("events_api", broker=REDIS_URL)

# Optional: load custom config from Django settings with prefix CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in installed apps
app.autodiscover_tasks()

# Simple beat schedule (seconds) — you can tweak these
app.conf.beat_schedule = {
    "scrape-every-30-mins": {
        "task": "events.tasks.run_scraper_task",
        "schedule": 30 * 60.0,  # 30 minutes
    },
    "mark-inactive-daily": {
        "task": "events.tasks.mark_inactive_task",
        "schedule": 24 * 60 * 60.0,  # once per day
    },
}

# optional: set timezone if needed
app.conf.timezone = "UTC"
