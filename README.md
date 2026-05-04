# Google Play Store App Analysis

Queue-based scraper for discovering Google Play app IDs across the 10 priority
markets, then extracting full details only for apps with 100,000+ installs.

## Goal

Build a broad dataset for app-market analysis:

- discover many app IDs, not only top-chart apps
- keep a queue so scraping can stop/resume
- fetch full app details
- save only apps with `minInstalls >= 100000`
- collect country stats for the 10 focus countries

## Focus Countries

```text
us, in, br, id, mx, gb, de, jp, kr, ph
```

These balance large Android markets and monetization-heavy markets.

## Main Tables

- `app_queue`: all discovered app IDs and processing status
- `discovery_signals`: where each app ID was discovered
- `apps`: full details for apps with 100k+ installs
- `app_country_stats`: country-wise stats for saved apps

## Setup

```powershell
pip install -r requirements.txt
python setup_db.py
python test_proxy.py
```

`.env` should contain:

```env
DB_USER=postgres
DB_PASS=your_postgres_password
DB_NAME=playstore
DB_HOST=localhost
DB_PORT=5433
WEBSHARE_PROXIES=http://user1:pass1@p.webshare.io:80,http://user2:pass2@p.webshare.io:80,http://user3:pass3@p.webshare.io:80
```

## Run

First discover app IDs:

```powershell
python discover_ids.py
```

Then extract and save 100k+ app details:

```powershell
python extract_details.py
```

Test a small extraction batch:

```powershell
python extract_details.py 20
```

Analyze current data:

```powershell
python analyze.py
```

## Reset Data

This clears the scraped PostgreSQL dataset:

```powershell
python reset_data.py
```
