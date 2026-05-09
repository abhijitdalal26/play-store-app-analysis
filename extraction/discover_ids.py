import re
import time
import requests
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_play_scraper import search
from fake_useragent import UserAgent
from core.config import (
    MARKET_COUNTRIES, CATEGORIES, CHART_COLLECTIONS, CHART_COUNT,
    build_search_keywords, SEARCH_HITS, THREADS
)
from core.db import DatabaseManager

ua = UserAgent()

APP_ID_RE = re.compile(r"(?:/store/apps/details\?id=|\\u003d)([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)")
VALID_APP_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")

def valid_app_id(app_id):
    return bool(app_id and VALID_APP_ID_RE.match(app_id))

def get_random_headers():
    return {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}

def discover_from_page(db, country, category, collection):
    country_code = country.upper()
    urls = [
        f"https://play.google.com/store/apps/collection/{collection}?c={category}&hl=en&gl={country_code}",
        f"https://play.google.com/store/apps/category/{category}?hl=en&gl={country_code}",
    ]
    found = 0
    seen = set()
    for url in urls:
        time.sleep(1) # Delay to avoid bans
        try:
            resp = requests.get(url, headers=get_random_headers(), timeout=45)
            resp.raise_for_status()
            for app_id in APP_ID_RE.findall(resp.text):
                if app_id in seen or not valid_app_id(app_id):
                    continue
                seen.add(app_id)
                found += 1
                db.add_discovery(app_id=app_id, source="chart_page", country=country, category=category, collection=collection, chart_rank=found)
                if found >= CHART_COUNT:
                    return found
        except Exception as e:
            print(f"[chart:error] {country} {category} {collection}: {e}")
            raise
    return found

def discover_from_search(db, country, keyword):
    found = 0
    try:
        time.sleep(1)
        results = search(keyword, n_hits=SEARCH_HITS, lang="en", country=country)
        for rank, item in enumerate(results, start=1):
            app_id = item.get("appId")
            if not valid_app_id(app_id):
                continue
            found += 1
            db.add_discovery(app_id=app_id, source="search", country=country, keyword=keyword, chart_rank=rank)
    except Exception as e:
        print(f"[search:error] {country} {keyword}: {e}")
        raise
    return found

def worker_chart_pages(task, db):
    country, category, collection = task
    if db.is_discovery_task_done("chart_page", country=country, category=category, collection=collection):
        return f"[chart:skip] {country} {category} {collection}"
    try:
        count = discover_from_page(db, country, category, collection)
        db.mark_discovery_task("chart_page", country=country, category=category, collection=collection, app_count=count)
        return f"[chart] {country} {category} {collection}: {count}"
    except Exception as exc:
        db.mark_discovery_task("chart_page", country=country, category=category, collection=collection, status="failed", error=str(exc)[:1000])
        return f"[chart:fail] {country} {category} {collection}: {exc}"

def worker_search(task, db):
    country, keyword = task
    if db.is_discovery_task_done("search", country=country, keyword=keyword):
        return f"[search:skip] {country} {keyword}"
    try:
        count = discover_from_search(db, country, keyword)
        db.mark_discovery_task("search", country=country, keyword=keyword, app_count=count)
        return f"[search] {country} {keyword}: {count}"
    except Exception as exc:
        db.mark_discovery_task("search", country=country, keyword=keyword, status="failed", error=str(exc)[:1000])
        return f"[search:fail] {country} {keyword}: {exc}"

def main():
    db = DatabaseManager()
    db.create_tables()

    tasks_chart = [(co, ca, col) for co in MARKET_COUNTRIES for ca in CATEGORIES for col in CHART_COLLECTIONS]
    tasks_search = [(co, kw) for co in MARKET_COUNTRIES for kw in build_search_keywords(co)]

    print(f"[discover] Starting chart discovery with {THREADS} threads...")
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(worker_chart_pages, t, db) for t in tasks_chart]
        for future in as_completed(futures):
            print(future.result())

    print(f"[discover] Starting search discovery with {THREADS} threads...")
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(worker_search, t, db) for t in tasks_search]
        for future in as_completed(futures):
            print(future.result())

    print("[discover] Counts:", db.counts())
    db.close()

if __name__ == "__main__":
    main()
