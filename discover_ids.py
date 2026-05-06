"""
discover_ids.py - Build a broad app_id queue from charts, categories, and search.
Supports parallel discovery with multiple proxy sources (Webshare + Direct IP).
Usage: python discover_ids.py
"""
import re
import time
import requests
import threading
import queue
from google_play_scraper import search
from config import (
    MARKET_COUNTRIES, CATEGORIES, CHART_COLLECTIONS, CHART_COUNT,
    build_search_keywords, SEARCH_HITS, PROXY_MODE,
)
from db import DatabaseManager
from proxies import (
    get_random_headers, get_webshare_proxy, webshare_env_proxy,
    get_proxy_for_source, apply_request_delay, env_proxy_for_source,
    random_delay
)

APP_ID_RE = re.compile(r"(?:/store/apps/details\?id=|\\u003d)([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)")
VALID_APP_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")


def valid_app_id(app_id):
    return bool(app_id and VALID_APP_ID_RE.match(app_id))


def discover_from_page(db, country, category, collection, source="webshare"):
    """Discover apps from chart/category pages using specified proxy source."""
    country_code = country.upper()
    urls = [
        f"https://play.google.com/store/apps/collection/{collection}?c={category}&hl=en&gl={country_code}",
        f"https://play.google.com/store/apps/category/{category}?hl=en&gl={country_code}",
    ]
    found = 0
    seen = set()
    for url in urls:
        apply_request_delay(source)
        try:
            proxy = get_proxy_for_source(source)
            resp = requests.get(url, headers=get_random_headers(), proxies=proxy, timeout=45)
            resp.raise_for_status()
            for app_id in APP_ID_RE.findall(resp.text):
                if app_id in seen or not valid_app_id(app_id):
                    continue
                seen.add(app_id)
                found += 1
                db.add_discovery(
                    app_id=app_id,
                    source="chart_page",
                    country=country,
                    category=category,
                    collection=collection,
                    chart_rank=found,
                )
                if found >= CHART_COUNT:
                    return found
        except Exception as e:
            print(f"[{source}:page:error] {country} {category} {collection}: {e}")
            raise
    return found


def discover_from_search(db, country, keyword, source="webshare"):
    """Discover apps from search using specified proxy source."""
    found = 0
    try:
        with env_proxy_for_source(source):
            apply_request_delay(source)
            results = search(keyword, n_hits=SEARCH_HITS, lang="en", country=country)
        for rank, item in enumerate(results, start=1):
            app_id = item.get("appId")
            if not valid_app_id(app_id):
                continue
            found += 1
            db.add_discovery(
                app_id=app_id,
                source="search",
                country=country,
                keyword=keyword,
                chart_rank=rank,
            )
    except Exception as e:
        print(f"[{source}:search:error] {country} {keyword}: {e}")
        raise
    return found


def worker_chart_pages(source, task_queue, db):
    """Worker thread for discovering from chart pages using specified proxy source."""
    while True:
        try:
            task = task_queue.get_nowait()
        except queue.Empty:
            break
        
        country, category, collection = task
        if db.is_discovery_task_done("chart_page", country=country, category=category, collection=collection):
            print(f"[{source}:chart:skip] {country} {category} {collection}")
            task_queue.task_done()
            continue
        
        try:
            count = discover_from_page(db, country, category, collection, source=source)
            db.mark_discovery_task("chart_page", country=country, category=category, collection=collection, app_count=count)
            print(f"[{source}:chart] {country} {category} {collection}: {count}")
        except Exception as exc:
            db.mark_discovery_task("chart_page", country=country, category=category, collection=collection, status="failed", error=str(exc)[:1000])
            print(f"[{source}:chart:fail] {country} {category} {collection}: {exc}")
        finally:
            random_delay()
            task_queue.task_done()


def worker_search(source, task_queue, db):
    """Worker thread for discovering from search using specified proxy source."""
    while True:
        try:
            task = task_queue.get_nowait()
        except queue.Empty:
            break
        
        country, keyword = task
        if db.is_discovery_task_done("search", country=country, keyword=keyword):
            print(f"[{source}:search:skip] {country} {keyword}")
            task_queue.task_done()
            continue
        
        try:
            count = discover_from_search(db, country, keyword, source=source)
            db.mark_discovery_task("search", country=country, keyword=keyword, app_count=count)
            print(f"[{source}:search] {country} {keyword}: {count}")
        except Exception as exc:
            db.mark_discovery_task("search", country=country, keyword=keyword, status="failed", error=str(exc)[:1000])
            print(f"[{source}:search:fail] {country} {keyword}: {exc}")
        finally:
            random_delay()
            task_queue.task_done()


def discover_charts_parallel(db):
    """Discover from charts using parallel proxy sources."""
    print(f"[discover] Starting chart discovery with PROXY_MODE={PROXY_MODE}")
    
    task_queue = queue.Queue()
    for country in MARKET_COUNTRIES:
        for category in CATEGORIES:
            for collection in CHART_COLLECTIONS:
                task_queue.put((country, category, collection))
    
    threads = []
    if PROXY_MODE in ("webshare_only", "dual"):
        t = threading.Thread(target=worker_chart_pages, args=("webshare", task_queue, db), daemon=False)
        threads.append(t)
        t.start()
    
    if PROXY_MODE in ("direct_only", "dual"):
        t = threading.Thread(target=worker_chart_pages, args=("direct", task_queue, db), daemon=False)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()


def discover_search_parallel(db):
    """Discover from search using parallel proxy sources."""
    print(f"[discover] Starting search discovery with PROXY_MODE={PROXY_MODE}")
    
    task_queue = queue.Queue()
    for country in MARKET_COUNTRIES:
        for keyword in build_search_keywords(country):
            task_queue.put((country, keyword))
    
    threads = []
    if PROXY_MODE in ("webshare_only", "dual"):
        t = threading.Thread(target=worker_search, args=("webshare", task_queue, db), daemon=False)
        threads.append(t)
        t.start()
    
    if PROXY_MODE in ("direct_only", "dual"):
        t = threading.Thread(target=worker_search, args=("direct", task_queue, db), daemon=False)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()


def main():
    db = DatabaseManager()
    db.create_tables()

    try:
        discover_charts_parallel(db)
        discover_search_parallel(db)
        print("[discover] Counts:", db.counts())
    finally:
        db.close()


if __name__ == "__main__":
    main()
