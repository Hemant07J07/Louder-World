# events/management/commands/run_scraper.py
from django.core.management.base import BaseCommand
from events.tasks import run_scraper_task

class Command(BaseCommand):
    help = "Run scraper synchronously via Celery task (for local testing)."

    def handle(self, *args, **options):
        # Run the task synchronously (not via worker) to reuse the same code path
        res = run_scraper_task.apply()  # runs task immediately
        print(res.get())
