from celery import Celery
import os

CELERY_BROKER = os.environ.get("CELERY_BROKER", "redis://localhost:6379/0")
app = Celery("event_scraper", broken=CELERY_BROKER)

@app.task
def scrape_once_task():
    from .main import run_once
    return run_once()