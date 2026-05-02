# Google Play Store Scraper — Full Implementation Plan

## Project Goal
Scrape ~175,000 apps (100K+ installs) × 30 countries = **~5.25 million rows** for data analysis across 5 dimensions:
1. Download trends over time
2. Country-wise app popularity
3. Category/genre trends
4. Top rising apps
5. Revenue & monetization

**Hardware:** Raspberry Pi 4B, 4GB RAM, 32GB SD Card, 24/7 always-on.
**Access:** SSH from laptop.

---

## ✅ Database Decision: DuckDB

**DuckDB is the perfect choice for this project.**

| Criteria | DuckDB ✅ | SQLite ❌ | PostgreSQL ❌ |
|---|---|---|---|
| Analytical queries (AVG, GROUP BY, window functions) | 🚀 Vectorized, extremely fast | Slow on millions of rows | OK, but overkill |
| RAM usage on Pi | Efficient (configurable) | Very low | High (server process) |
| Setup | `pip install duckdb` — zero config | Built-in | Install + config server |
| Storage format | Single `.duckdb` file | Single `.db` file | Server-managed |
| Works offline/embedded | ✅ Yes | ✅ Yes | ❌ Needs server |
| Built-in Parquet/CSV export for analysis | ✅ Native | ❌ No | ❌ No |
| Best for | **Analytics** | CRUD apps | Production web apps |

**Why DuckDB wins:** Your end goal is analysis — aggregations, trends, rankings across 5M+ rows. DuckDB uses columnar vectorized execution and is 10–50x faster than SQLite for these queries. It runs embedded (no server process), so it won't eat the Pi's limited RAM.

---

## ⚠️ Honest Proxy Reality Check

> **Webshare free plan = 10 datacenter proxies + only 1GB/month bandwidth.**
> This is NOT enough for the full scrape. Here is the actual plan for maximizing free resources:

| Proxy Source | Type | Quality | Limit | Strategy |
|---|---|---|---|---|
| **Webshare.io** (free) | Datacenter (10 IPs) | Medium | 1GB/month | Use for Phase 1 charts only |
| **proxyscrape.com** | Public shared | Low (30–50% working) | Unlimited but unreliable | Refresh hourly, test before use |
| **Tor Network** | Residential-like | Medium | Slow (~1 req/5s) | Primary for Phase 2 details |
| **Home IP** | Residential | High | Risk of ban | Last-resort fallback only |

**Expected result:** With Tor as primary, you get real rotating IPs at no cost. Speed drops to ~30–60 req/min (vs 150 target), so Phase 2 takes **48–72 hours** instead of 24 hours. Since the Pi runs 24/7, this is totally acceptable.

---

## Storage Estimate on 32GB SD Card

| Item | Estimated Size |
|---|---|
| Raspberry Pi OS | ~3–4 GB |
| Python + libraries | ~500 MB |
| DuckDB file (5.25M rows) | ~3–4 GB |
| Log files | ~200 MB |
| Checkpoint files | ~50 MB |
| **Total used** | **~8–9 GB** |
| **Remaining free** | **~23 GB ✅** |

32GB SD card is sufficient. No external USB or Google Drive needed during scraping — though a weekly backup to Google Drive is recommended.

---

## Dataset Decisions

| Parameter | Value |
|---|---|
| Target apps | Only apps with 100,000+ downloads |
| Estimated app count | ~150,000–175,000 apps |
| Countries | 30 (covering 95% of Play Store activity) |
| Categories | 15 |
| Total estimated rows | ~5.25 million (175K apps × 30 countries) |
| Fields per app | All 40 fields returned by google-play-scraper |
| Storage estimate | ~3–4 GB |

---

## 30 Countries

| Tier | Countries |
|---|---|
| **Tier 1 — Must Have** | US, IN, BR, ID, RU |
| **Tier 2 — Big Markets** | DE, FR, GB, JP, KR, MX, TR, VN, TH, PH |
| **Tier 3 — Emerging** | NG, ZA, EG, PK, BD, AR, CO, SA, AE |
| **Tier 4 — High Revenue** | CA, AU, IT, ES, NL, PL, SE |

---

## 15 Categories

```
SOCIAL, FINANCE, TOOLS, GAME, ENTERTAINMENT, SHOPPING, EDUCATION,
HEALTH_AND_FITNESS, TRAVEL_AND_LOCAL, FOOD_AND_DRINK, PRODUCTIVITY,
COMMUNICATION, MAPS_AND_NAVIGATION, MUSIC_AND_AUDIO, PHOTOGRAPHY
```

---

## Database Schema (DuckDB — 3 Tables)

### Table 1: `apps`
Stores all 40 fields for each unique app. **One row per app.**

```sql
CREATE TABLE IF NOT EXISTS apps (
    app_id                      VARCHAR PRIMARY KEY,
    title                       VARCHAR,
    description                 TEXT,
    summary                     VARCHAR,
    installs                    VARCHAR,        -- e.g. "10,000,000+"
    min_installs                BIGINT,         -- parsed integer
    max_installs                BIGINT,
    score                       DOUBLE,
    ratings                     BIGINT,
    reviews                     BIGINT,
    histogram                   JSON,           -- {1:N, 2:N, 3:N, 4:N, 5:N}
    price                       DOUBLE,
    free                        BOOLEAN,
    currency                    VARCHAR,
    sale                        BOOLEAN,
    sale_time                   VARCHAR,
    original_price              DOUBLE,
    developer                   VARCHAR,
    developer_id                VARCHAR,
    developer_email             VARCHAR,
    developer_website           VARCHAR,
    developer_address           VARCHAR,
    privacy_policy              VARCHAR,
    genre                       VARCHAR,
    genre_id                    VARCHAR,
    categories                  JSON,           -- list of categories
    icon                        VARCHAR,
    header_image                VARCHAR,
    screenshots                 JSON,
    video                       VARCHAR,
    video_image                 VARCHAR,
    content_rating              VARCHAR,
    content_rating_description  VARCHAR,
    ad_supported                BOOLEAN,
    contains_ads                BOOLEAN,
    in_app_purchases            BOOLEAN,
    size                        VARCHAR,
    android_version             VARCHAR,
    android_version_text        VARCHAR,
    developer_internal_id       VARCHAR,
    required_android_version    VARCHAR,
    interactive_elements        VARCHAR,
    updated                     BIGINT,         -- unix timestamp
    version                     VARCHAR,
    recent_changes              TEXT,
    scraped_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table 2: `app_country_stats`
Per-country stats per scrape run. **Primary key = (app_id, country, scraped_at).**

```sql
CREATE TABLE IF NOT EXISTS app_country_stats (
    app_id          VARCHAR,
    country         VARCHAR(2),     -- ISO country code e.g. 'us', 'in'
    installs        VARCHAR,
    min_installs    BIGINT,
    score           DOUBLE,
    ratings         BIGINT,
    reviews         BIGINT,
    price           DOUBLE,
    free            BOOLEAN,
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_id, country, scraped_at)
);
```

### Table 3: `country_charts`
Top chart snapshots per country, category, and scrape date.

```sql
CREATE TABLE IF NOT EXISTS country_charts (
    country         VARCHAR(2),
    category        VARCHAR,
    chart_type      VARCHAR,        -- 'top_free', 'top_paid', 'grossing'
    chart_rank      INTEGER,
    app_id          VARCHAR,
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (country, category, chart_type, chart_rank, scraped_at)
);
```

---

## Scraping Tool & Strategy

| Parameter | Value |
|---|---|
| Library | `google-play-scraper` (Python) |
| Threads | 8 parallel threads |
| Speed | ~30–60 req/min (Tor-limited) |
| Anti-ban | Random delays 2.5–7s, proxy rotation, randomized user agents |
| Progress saving | Checkpoint files, saved every completed app |

---

## Proxy Rotation Strategy (3 Free Sources)

| Source | Role |
|---|---|
| **Webshare.io** — 10 free datacenter proxies | Phase 1 only (conserve 1GB bandwidth limit) |
| **proxyscrape.com** — public proxy pool, refreshed hourly | Phase 1 & 2 fallback |
| **Tor Network** — circuit renewed every 10 requests | Phase 2 primary (free, real IP rotation) |

**Tor setup on Pi (one-time):**
```bash
sudo apt install tor
# Add to /etc/tor/torrc:
#   ControlPort 9051
#   HashedControlPassword (generate with: tor --hash-password "yourpassword")
sudo systemctl restart tor
```
Python communicates via SOCKS5 at `127.0.0.1:9050` and renews circuits via the control port using the `stem` library.

---

## Two-Phase Scraping Plan

### Phase 1 — Scrape Top Charts (3–5 hours)

- 30 countries × 15 categories × 3 chart types = **1,350 combinations**
- Fetch top 200 apps per combination
- Save to `country_charts` table
- Collect all unique app IDs → write to `phase2_queue.txt`
- **Total requests:** ~9,000
- **Proxy used:** Webshare (conserves bandwidth) + public fallback

### Phase 2 — Scrape App Details (48–72 hours)

- Read all unique app IDs from `phase2_queue.txt`
- For each app ID:
  - Fetch all 40 fields
  - Filter: keep only apps with `min_installs >= 100,000`
  - Fetch country-specific stats for all 30 countries
  - Save to `apps` + `app_country_stats` tables
  - Mark as done in `phase2_done.txt`
- **Proxy used:** Tor (primary), public proxies (fallback)
- **Resumable:** Crashes can resume from last checkpoint

---

## Full File Structure on Pi

```
/home/pi/playstore_scraper/
├── config.py               # All settings, countries, categories, thresholds
├── db.py                   # DuckDB connection, schema creation, upsert methods
├── proxies.py              # Proxy pool manager (Webshare + proxyscrape + Tor)
├── checkpoint.py           # Save/load/resume progress
├── phase1_charts.py        # Phase 1: scrape top charts
├── phase2_details.py       # Phase 2: scrape full app details
├── requirements.txt        # Python dependencies
├── phase1.log              # Auto-generated Phase 1 logs
├── phase2.log              # Auto-generated Phase 2 logs
├── checkpoints/
│   ├── phase1_done.txt     # country,category,chart_type combos completed
│   ├── phase2_queue.txt    # All unique app IDs discovered in Phase 1
│   └── phase2_done.txt     # App IDs fully scraped
└── playstore.duckdb        # Main database file
```

---

## Module Responsibilities

### `config.py`
- Lists for all 30 countries, 15 categories, 3 chart types
- Constants: `MIN_INSTALLS`, `THREADS`, `DELAY_MIN`, `DELAY_MAX`, `RETRY_LIMIT`
- File paths: `DB_PATH`, `CHECKPOINT_DIR`
- Webshare proxy credentials

### `db.py`
- `create_tables()` — runs schema SQL on startup
- `upsert_app(data)` — insert or ignore into `apps`
- `upsert_country_stats(app_id, country, data)` — insert into `app_country_stats`
- `insert_chart_entry(...)` — insert into `country_charts`
- `get_all_chart_app_ids()` — returns set for Phase 2 queue
- `app_already_scraped(app_id)` — deduplication check

### `proxies.py`
- `load_webshare_proxies()` — from config
- `load_public_proxies()` — fetch from proxyscrape.com, refresh every hour
- `test_proxy(proxy)` — health check via httpbin.org/ip
- `get_next_proxy()` — round-robin rotation
- `renew_tor_circuit()` — send NEWNYM via stem library
- `mark_proxy_failed(proxy)` — remove and trigger pool refresh

### `checkpoint.py`
- `mark_phase1_done(country, category, chart_type)`
- `is_phase1_done(country, category, chart_type) → bool`
- `write_phase2_queue(app_ids: set)`
- `get_phase2_remaining() → list`
- `mark_phase2_done(app_id)`

### `phase1_charts.py`
- Main loop: 30 × 15 × 3 = 1,350 combinations
- Skip if already in checkpoint
- Fetch charts → save to DB → mark checkpoint
- At end: collect unique app IDs → write phase2 queue

### `phase2_details.py`
- Load remaining app IDs from checkpoint
- `ThreadPoolExecutor` with 8 workers
- Per app: fetch details → filter by installs → save to DB → mark done
- Per country (30): fetch country stats → save to DB
- Exponential backoff on rate-limit errors

---

## Retry & Backoff Logic

| Attempt | Wait | Action |
|---|---|---|
| 1 | 0s | Normal request |
| 2 | 10s | Switch proxy |
| 3 | 30s | Renew Tor circuit |
| 4 | 60s | Try Tor again |
| 5 | 120s | Log as failed, move to next app |

---

## Anti-Ban Strategy

| Technique | Implementation |
|---|---|
| Random delays | `random.uniform(2.5, 7.0)` seconds between requests |
| Rotating user agents | `fake-useragent` library — new UA every request |
| IP rotation | Tor circuit renewal every 10 requests |
| Proxy fallback chain | Webshare → Public → Tor → backoff |
| Exponential backoff | On 429: 10s → 30s → 60s → 120s → skip |
| Thread limiting | 8 threads max (not 50) |
| Randomized order | Random shuffle of country/category order in Phase 1 |

---

## Python Requirements

```
google-play-scraper==1.2.7
duckdb>=0.10.0
requests>=2.31.0
stem>=1.8.2
fake-useragent>=1.5.1
```

Install on Pi:
```bash
pip3 install google-play-scraper duckdb requests stem fake-useragent
```

---

## How to Run on Pi

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Phase 1
cd /home/pi/playstore_scraper
nohup python3 phase1_charts.py > phase1.log 2>&1 &
tail -f phase1.log

# After Phase 1 completes (~3-5 hours), run Phase 2
nohup python3 phase2_details.py > phase2.log 2>&1 &
tail -f phase2.log

# Monitor progress
wc -l checkpoints/phase2_done.txt    # apps scraped so far
wc -l checkpoints/phase2_queue.txt  # total apps to scrape
```

---

## Data Flow Diagram

```
Phase 1                                Phase 2
─────────────────────────────────      ──────────────────────────────────────────
30 Countries                           phase2_queue.txt
  × 15 Categories           ──────→   (all unique app IDs, ~175,000)
  × 3 Chart Types                              │
= 1,350 chart fetches                         ▼
         │                          ThreadPoolExecutor (8 workers)
         ▼                                    │
 country_charts table              For each app_id:
 (chart rank snapshots)            ├── Fetch detail (40 fields) via proxy/Tor
         │                         ├── Filter: min_installs >= 100,000
         │                         ├── Save → `apps` table (once)
         └── collect unique        └── For each of 30 countries:
             app_ids                   ├── Fetch country-specific stats
                                       └── Save → `app_country_stats` table
```

---

## Expected Final Dataset

| Table | Rows | Estimated Size |
|---|---|---|
| `apps` | ~175,000 | ~800 MB |
| `app_country_stats` | ~5,250,000 | ~2.5 GB |
| `country_charts` | ~810,000 | ~400 MB |
| **Total** | **~6.2 million rows** | **~3.7 GB** |

---

## Sample Analysis Queries (After Scrape)

```sql
-- 1. Average rating by category
SELECT genre, ROUND(AVG(score), 2) AS avg_rating, COUNT(*) AS app_count
FROM apps GROUP BY genre ORDER BY avg_rating DESC;

-- 2. Top 20 apps by installs in India
SELECT a.title, s.min_installs
FROM apps a JOIN app_country_stats s ON a.app_id = s.app_id
WHERE s.country = 'in'
ORDER BY s.min_installs DESC LIMIT 20;

-- 3. Free vs paid breakdown
SELECT free, COUNT(*) AS count, ROUND(AVG(score), 2) AS avg_rating
FROM apps GROUP BY free;

-- 4. Apps appearing in top 50 charts in most countries (rising apps)
SELECT app_id, COUNT(DISTINCT country) AS country_count
FROM country_charts WHERE chart_rank <= 50
GROUP BY app_id ORDER BY country_count DESC LIMIT 20;

-- 5. Monetization breakdown
SELECT ad_supported, in_app_purchases, COUNT(*) AS count
FROM apps GROUP BY ad_supported, in_app_purchases ORDER BY count DESC;
```

---

## ✅ Pre-Coding Checklist

Before writing any code, confirm the following:

- [ ] Agree to use **DuckDB** as the database
- [ ] Agree to use **Tor** as primary proxy for Phase 2
- [ ] Sign up at [webshare.io](https://webshare.io) (free, no credit card) and obtain 10 proxy credentials
- [ ] Confirm Pi runs **Raspberry Pi OS 64-bit**

---

*Last updated: 2026-05-02*
