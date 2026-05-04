"""
discover_ids.py - Build a broad app_id queue from charts, categories, and search.
Usage: python discover_ids.py
"""
import re
import time
import requests
from google_play_scraper import search
from config import (
    MARKET_COUNTRIES, CATEGORIES, CHART_COLLECTIONS, CHART_COUNT,
    SEARCH_KEYWORDS, SEARCH_HITS,
)
from db import DatabaseManager
from proxies import get_random_headers, get_webshare_proxy, webshare_env_proxy, random_delay

APP_ID_RE = re.compile(r"(?:/store/apps/details\?id=|\\u003d)([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)")
VALID_APP_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")


def valid_app_id(app_id):
    return bool(app_id and VALID_APP_ID_RE.match(app_id))


def discover_from_page(db, country, category, collection):
    country_code = country.upper()
    urls = [
        f"https://play.google.com/store/apps/collection/{collection}?c={category}&hl=en&gl={country_code}",
        f"https://play.google.com/store/apps/category/{category}?hl=en&gl={country_code}",
    ]
    found = 0
    seen = set()
    for url in urls:
        resp = requests.get(url, headers=get_random_headers(), proxies=get_webshare_proxy(), timeout=45)
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
    return found


def discover_from_search(db, country, keyword):
    found = 0
    with webshare_env_proxy():
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
    return found


def main():
    db = DatabaseManager()
    db.create_tables()

    try:
        for country in MARKET_COUNTRIES:
            for category in CATEGORIES:
                for collection in CHART_COLLECTIONS:
                    try:
                        count = discover_from_page(db, country, category, collection)
                        print(f"[chart] {country} {category} {collection}: {count}")
                    except Exception as exc:
                        print(f"[chart:fail] {country} {category} {collection}: {exc}")
                    random_delay()

        for country in MARKET_COUNTRIES:
            for keyword in SEARCH_KEYWORDS:
                try:
                    count = discover_from_search(db, country, keyword)
                    print(f"[search] {country} {keyword}: {count}")
                except Exception as exc:
                    print(f"[search:fail] {country} {keyword}: {exc}")
                time.sleep(2)

        print("[discover] Counts:", db.counts())
    finally:
        db.close()


if __name__ == "__main__":
    main()
