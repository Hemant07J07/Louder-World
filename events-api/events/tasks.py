# events/tasks.py
from celery import shared_task
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from .mongo import events_coll
import traceback
import sys
from pathlib import Path

from .recommender import build_index


def _import_run_once():
	"""Import scraper.main.run_once, even if event-scraper isn't installed."""
	try:
		from scraper.main import run_once  # type: ignore
		return run_once
	except ModuleNotFoundError:
		repo_root = Path(__file__).resolve().parents[2]
		event_scraper_root = repo_root / "event-scraper"
		if str(event_scraper_root) not in sys.path:
			sys.path.insert(0, str(event_scraper_root))
		from scraper.main import run_once  # type: ignore
		return run_once


@shared_task
def run_scraper_task():
	"""
	Call the scraper.main.run_once() function (from your scraper package).
	This runs the scraper and upserts events into Mongo.
	"""
	try:
		# import inside task to avoid import-time side-effects
		run_once = _import_run_once()
		result = run_once()  # returns stats dict from scraper
		return {"status": "ok", "result": result}
	except Exception as e:
		return {"status": "error", "error": str(e), "trace": traceback.format_exc()}


@shared_task
def mark_inactive_task(days_threshold=7):
	"""
	Mark events as inactive if last_scraped_at is older than days_threshold.
	Does NOT overwrite events with status 'imported'.
	"""
	try:
		now = datetime.utcnow()
		cutoff = now - timedelta(days=int(days_threshold))
		updated = 0
		cursor = events_coll.find({"status": {"$ne": "imported"}})
		for doc in cursor:
			last = doc.get("last_scraped_at")
			if not last:
				continue
			try:
				dt = dateparser.parse(last)
			except Exception:
				continue
			if dt < cutoff:
				events_coll.update_one({"_id": doc["_id"]}, {"$set": {"status": "inactive"}})
				updated += 1
		return {"status": "ok", "updated": updated}
	except Exception as e:
		return {"status": "error", "error": str(e), "trace": traceback.format_exc()}


@shared_task
def rebuild_faiss_index():
	return build_index()
