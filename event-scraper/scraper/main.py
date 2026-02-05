# scraper/main.py
from datetime import datetime, timedelta

from .parsers import (
    fetch_url,
    parse_cityofsydney_whats_on_listing,
    parse_sydneycom_events_listing,
)
from .db import events_coll
from .utils import make_checksum, now_iso

SOURCES = [
    {
        "name": "CityOfSydney",
        "url": "https://whatson.cityofsydney.nsw.gov.au/",
        "base_url": "https://whatson.cityofsydney.nsw.gov.au",
        "parser": parse_cityofsydney_whats_on_listing,
    },
    {
        "name": "SydneyCom",
        "url": "https://www.sydney.com/events",
        "base_url": "https://www.sydney.com",
        "parser": parse_sydneycom_events_listing,
    },
]

def process_item(item, source_name):
    # normalize
    title = item.get("title")
    start_time = item.get("start_time")
    venue = item.get("venue")
    description = item.get("description")
    source_url = item.get("source_url")
    city = item.get("city") or "Sydney"
    tags = item.get("tags")

    checksum = make_checksum(title, str(start_time), venue, description, city, str(tags))

    query = {}
    if source_url:
        query = {"source_url": source_url}
    else:
        # fallback: by checksum if no source_url
        query = {"checksum": checksum}

    existing = events_coll.find_one(query)

    doc = {
        "title": title,
        "start_time": start_time.isoformat() if start_time else None,
        "venue": venue,
        "city": city,
        "description": description,
        "tags": tags,
        "image_url": item.get("image_url"),
        "source_url": source_url,
        "source_name": source_name,
        "last_scraped_at": now_iso(),
        "checksum": checksum
    }

    if not existing:
        doc.update({"status": "new", "created_at": now_iso()})
        events_coll.insert_one(doc)
        return "inserted"
    else:
        # If checksum changed -> updated
        if existing.get("checksum") != checksum:
            doc.update({"status": "updated", "created_at": existing.get("created_at")})
            events_coll.update_one({"_id": existing["_id"]}, {"$set": doc})
            return "updated"
        else:
            # unchanged, just update last_scraped_at
            events_coll.update_one({"_id": existing["_id"]}, {"$set": {"last_scraped_at": now_iso()}})
            return "unchanged"


def run_once():
    stats = {"inserted":0,"updated":0,"unchanged":0}
    for src in SOURCES:
        try:
            html = fetch_url(src["url"])
            items = src["parser"](html, src["base_url"])
            seen_urls = set()
            for it in items:
                res = process_item(it, src["name"])
                stats[res] += 1
                if it.get("source_url"):
                    seen_urls.add(it.get("source_url"))
            # after scraping items for a source: mark older events as inactive
            threshold_days = 7
            cutoff = datetime.utcnow() - timedelta(days=threshold_days)
            events_coll.update_many(
                {
                    "source_name": src["name"],
                    "last_scraped_at": {"$lt": cutoff.isoformat() + "Z"},
                    "status": {"$ne": "imported"},
                },
                {"$set": {"status": "inactive"}},
            )
        except Exception as e:
            print("Error scraping", src["name"], e)
    print("Done. stats:", stats)
    return stats

if __name__ == "__main__":
    run_once()
