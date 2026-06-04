"""
extract_details.py - App details scraper. Fetches full application metadata (US baseline) and country-specific stats (installs, ratings, prices) for queued app IDs, saving them to the database.
Usage: python -m extraction.extract_details [batch_limit]
"""
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_play_scraper import app as gps_app
from extraction.config import MARKET_COUNTRIES, THREADS, RETRY_LIMIT, MIN_INSTALLS, REQUEST_TIMEOUT
from extraction.db import DatabaseManager

socket.setdefaulttimeout(REQUEST_TIMEOUT)

def fetch_app(app_id, country):
    waits = [5, 15, 30, 60][:RETRY_LIMIT]
    for attempt, wait in enumerate(waits, start=1):
        try:
            return gps_app(app_id, lang="en", country=country)
        except Exception as exc:
            if attempt == len(waits):
                raise exc
            time.sleep(wait)

def process_app(app_id):
    db = DatabaseManager()
    try:
        detail = fetch_app(app_id, "us")
        min_installs = detail.get("minInstalls") or 0
        if min_installs < MIN_INSTALLS:
            db.mark_status(app_id, "skipped_low_installs", min_installs=min_installs)
            return f"SKIP {app_id} {min_installs}"

        db.upsert_app(detail)
        stats = []
        for country in MARKET_COUNTRIES:
            try:
                time.sleep(1)  # Minimal delay
                country_detail = fetch_app(app_id, country)
                stats.append({
                    "app_id": app_id,
                    "country": country,
                    "installs": country_detail.get("installs"),
                    "min_installs": country_detail.get("minInstalls"),
                    "score": country_detail.get("score"),
                    "ratings": country_detail.get("ratings"),
                    "reviews": country_detail.get("reviews"),
                    "price": country_detail.get("price"),
                    "free": country_detail.get("free"),
                })
            except Exception:
                continue
        db.insert_country_stats(stats)
        db.mark_status(app_id, "done", min_installs=min_installs)
        return f"DONE {app_id} {min_installs}"
    except Exception as exc:
        db.mark_status(app_id, "failed", error=str(exc)[:1000])
        return f"FAIL {app_id} {exc}"
    finally:
        db.close()

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    db = DatabaseManager()
    db.create_tables()
    app_ids = db.get_pending_app_ids(limit=limit)
    db.close()

    print(f"[extract] pending={len(app_ids)} min_installs={MIN_INSTALLS}")
    if not app_ids:
        return

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(process_app, app_id) for app_id in app_ids]
        for future in as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    main()
