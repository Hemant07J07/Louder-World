import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "events_api.settings")

app = Celery("events_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Optional periodic tasks
app.conf.beat_schedule = getattr(app.conf, "beat_schedule", {})
app.conf.beat_schedule.update(
	{
		"scrape-events-every-30-min": {
			"task": "events.tasks.run_scraper_task",
			"schedule": 30 * 60.0,
		},
		"mark-inactive-daily": {
			"task": "events.tasks.mark_inactive_task",
			"schedule": 24 * 60 * 60.0,
		},
		"rebuild-index-nightly": {
			"task": "events.tasks.rebuild_faiss_index",
			"schedule": 24 * 60 * 60.0,
		},
	}
)
