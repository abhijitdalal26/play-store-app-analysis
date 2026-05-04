# Google Play Store Scraper — Updated Windows Implementation Plan

## Summary of Changes
| Item | Old Plan | ✅ New Plan |
|---|---|---|
| Database | DuckDB only | **PostgreSQL** (storage) + **DuckDB** (analysis) |
| Webshare proxies | 10 (1 account) | **20–30** (2–3 accounts) |
| Tor setup | Manual | **Automated via `setup_tor.ps1`** |
| Sleep settings | Pending | ✅ Already done |
| Checkpoint/Resume | Basic | **Full resume-from-crash system** |
| Hardware | Raspberry Pi | **Windows Laptop** |

---

## 🗄️ Database Decision: PostgreSQL + DuckDB (Industry Standard)

The industry-standard approach for a data analysis project at this scale is a two-layer database stack:

| Database | Role | Why |
|---|---|---|
| **PostgreSQL** | Primary storage — all scraped data written here | True industry standard RDBMS. Used by every major data team. Connects to every BI/viz tool (Tableau, Power BI, Grafana, Metabase, pgAdmin). ACID-safe, reliable, enforces data integrity. |
| **DuckDB** | Analysis layer — reads from PostgreSQL for fast analytical queries | Purpose-built for fast aggregations on millions of rows. Runs in-process. 10–50x faster than PostgreSQL for GROUP BY, window functions, and trend analysis. |

> **This is the exact two-layer pattern used in professional data engineering teams:** PostgreSQL as your system of record (reliable writes, relationships, constraints) and DuckDB as your analytical query engine (blazing-fast reads). You get the best of both worlds.

### PostgreSQL Setup (Windows — Local)
- Download installer: [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
- Simple `.exe` installer — set a password during setup, keep default port `5432`.
- No complex configuration needed.

---

## 🔄 Proxy Strategy — 20–30 Free Proxies (3 Webshare Accounts)

Using all 3 Webshare accounts gives us 30 proxies — far better than 10. More proxies = less per-IP rate limiting and faster Phase 1.

| Source | Proxies | Role | Quality |
|---|---|---|---|
| **Webshare.io Account 1** | 10 | Phase 1 + Phase 2 fallback | Medium (datacenter) |
| **Webshare.io Account 2** | 10 | Phase 1 + Phase 2 fallback | Medium (datacenter) |
| **Webshare.io Account 3** | 10 | Phase 1 + Phase 2 fallback | Medium (datacenter) |
| **Tor Network** | ∞ rotating | Phase 2 **primary** | High (residential-like) |
| **proxyscrape.com** | ~100–200 | Last resort fallback | Low (unreliable) |

**Rotation logic:**
- Phase 1: Round-robin across all 30 Webshare proxies.
- Phase 2: Tor as primary (circuit renewed every 10 requests) → Webshare fallback → proxyscrape fallback.
- On 429/block: exponential backoff: `10s → 30s → 60s → 120s → skip app`.

---

## 🔧 Tor Setup — Fully Automated

A `setup_tor.ps1` PowerShell script will:
1. Download the Tor Expert Bundle for Windows automatically.
2. Extract it to `C:\Tor\`.
3. Write the correct `torrc` configuration file.
4. Start Tor as a background Windows service.
5. Test the connection and print your Tor exit IP to confirm it works.

**You run one command and it's done:**
```powershell
.\setup_tor.ps1
```

---

## ✅ Checkpoint & Resume System

This is the most critical reliability feature. **Maximum data loss on a crash: 1 app.**

### Checkpoint Files
```
checkpoints/
├── phase1_done.txt      # One line per completed combo: "us,GAME,top_free"
├── phase2_queue.txt     # All ~175,000 app IDs (written once after Phase 1)
├── phase2_done.txt      # One line per completed app_id
└── phase2_failed.txt    # App IDs that failed all retries (logged and skipped)
```

### How Resume Works
- **Phase 1** reads `phase1_done.txt` → skips completed country/category/chart combos → resumes from next pending combo.
- **Phase 2** reads `phase2_queue.txt` minus `phase2_done.txt` → builds remaining list → resumes exactly where it stopped.
- Checkpoint file is written **immediately after each successful DB insert** — never in batches.

### Resume Command
```powershell
# Just re-run the exact same command. It auto-detects and resumes.
python phase2_details.py
# Output: "Resuming. 43,217 done. 131,783 remaining. Est. 38 hours left."
```

---

## 📁 Full File Structure

```
D:\Projects\play-store-analysis\
├── setup_tor.ps1           # Automated Tor installation & configuration
├── setup_db.py             # Creates PostgreSQL database, tables, and indexes
├── config.py               # All settings: paths, countries, categories, proxy list
├── db.py                   # PostgreSQL connection + all upsert/insert methods
├── proxies.py              # 30 Webshare + Tor + proxyscrape rotation logic
├── checkpoint.py           # Full resume-from-crash checkpoint manager
├── phase1_charts.py        # Phase 1: chart scraper → PostgreSQL
├── phase2_details.py       # Phase 2: app detail scraper → PostgreSQL
├── analyze.py              # DuckDB connects to PostgreSQL for analytics queries
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── IMPLEMENTATION_PLAN.md  # This document
└── checkpoints/            # Auto-created on first run
    ├── phase1_done.txt
    ├── phase2_queue.txt
    ├── phase2_done.txt
    └── phase2_failed.txt
```

---

## 🗃️ Database Schema — PostgreSQL (3 Tables)

### Table 1: `apps`
All 40 fields per unique app. **Primary key: `app_id`.**

```sql
CREATE TABLE IF NOT EXISTS apps (
    app_id                      TEXT PRIMARY KEY,
    title                       TEXT,
    description                 TEXT,
    summary                     TEXT,
    installs                    TEXT,
    min_installs                BIGINT,
    max_installs                BIGINT,
    score                       DOUBLE PRECISION,
    ratings                     BIGINT,
    reviews                     BIGINT,
    histogram                   JSONB,
    price                       DOUBLE PRECISION,
    free                        BOOLEAN,
    currency                    TEXT,
    sale                        BOOLEAN,
    sale_time                   TEXT,
    original_price              DOUBLE PRECISION,
    developer                   TEXT,
    developer_id                TEXT,
    developer_email             TEXT,
    developer_website           TEXT,
    developer_address           TEXT,
    privacy_policy              TEXT,
    genre                       TEXT,
    genre_id                    TEXT,
    categories                  JSONB,
    icon                        TEXT,
    header_image                TEXT,
    screenshots                 JSONB,
    video                       TEXT,
    video_image                 TEXT,
    content_rating              TEXT,
    content_rating_description  TEXT,
    ad_supported                BOOLEAN,
    contains_ads                BOOLEAN,
    in_app_purchases            BOOLEAN,
    size                        TEXT,
    android_version             TEXT,
    android_version_text        TEXT,
    developer_internal_id       TEXT,
    required_android_version    TEXT,
    interactive_elements        TEXT,
    updated                     BIGINT,
    version                     TEXT,
    recent_changes              TEXT,
    scraped_at                  TIMESTAMPTZ DEFAULT NOW()
);
```

### Table 2: `app_country_stats`
Per-country, per-scrape stats. **Primary key: `(app_id, country, scraped_date)`.**

```sql
CREATE TABLE IF NOT EXISTS app_country_stats (
    id              BIGSERIAL PRIMARY KEY,
    app_id          TEXT REFERENCES apps(app_id),
    country         CHAR(2),
    installs        TEXT,
    min_installs    BIGINT,
    score           DOUBLE PRECISION,
    ratings         BIGINT,
    reviews         BIGINT,
    price           DOUBLE PRECISION,
    free            BOOLEAN,
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (app_id, country, DATE(scraped_at))
);
CREATE INDEX idx_country_stats_app     ON app_country_stats(app_id);
CREATE INDEX idx_country_stats_country ON app_country_stats(country);
```

### Table 3: `country_charts`
Top chart snapshots. **Primary key: `(country, category, chart_type, chart_rank, scraped_date)`.**

```sql
CREATE TABLE IF NOT EXISTS country_charts (
    id              BIGSERIAL PRIMARY KEY,
    country         CHAR(2),
    category        TEXT,
    chart_type      TEXT,       -- 'top_free', 'top_paid', 'grossing'
    chart_rank      INTEGER,
    app_id          TEXT,
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (country, category, chart_type, chart_rank, DATE(scraped_at))
);
CREATE INDEX idx_charts_country  ON country_charts(country);
CREATE INDEX idx_charts_category ON country_charts(category);
```

---

## 📦 Python Dependencies

```
# requirements.txt
google-play-scraper==1.2.7
psycopg2-binary>=2.9.9
duckdb>=0.10.0
requests>=2.31.0
stem>=1.8.2
fake-useragent>=1.5.1
tqdm>=4.66.0
```

> `tqdm` added for real-time progress bars with ETA in the terminal.

---

## 🚀 Execution Plan (Step by Step)

### Step 1 — One-time Setup (~30 minutes)
```powershell
# 1. Download & install PostgreSQL from postgresql.org (set password: remember it)
# 2. Run automated Tor setup script
.\setup_tor.ps1
# 3. Install Python dependencies
pip install -r requirements.txt
# 4. Create PostgreSQL database and all 3 tables
python setup_db.py
```

### Step 2 — Add Proxy Credentials
Edit `config.py` → paste all 20–30 Webshare proxies.

### Step 3 — Run Phase 1 (3–5 hours)
```powershell
python phase1_charts.py
```
Progress bar shows: `[██████░░░] 450/1350 combos | 33% | ETA: 3h 12m`

### Step 4 — Run Phase 2 (48–72 hours, resumable)
```powershell
python phase2_details.py
```
Progress bar shows: `[████░░░░░] 43217/175000 apps | 24% | ETA: 51h 20m`

### Step 5 — Analyze Data
```powershell
python analyze.py
```
DuckDB connects to PostgreSQL and runs all 5 analysis queries.

---

## 🛡️ Anti-Ban Strategy

| Technique | Implementation |
|---|---|
| Random delays | `random.uniform(2.5, 7.0)` seconds between requests |
| IP rotation | 30 Webshare proxies (round-robin) + Tor every 10 requests |
| User-Agent rotation | `fake-useragent` — new UA every request |
| Thread limit | 10 threads max (no burst) |
| Exponential backoff | 10s → 30s → 60s → 120s → skip on 429 |
| Randomized order | Country/category order shuffled each run |
| Checkpoint safety | Write to DB + checkpoint after **every single app** |

---

## 📊 Data Flow Diagram

```
Phase 1 (3–5 hrs)                        Phase 2 (48–72 hrs)
──────────────────────────────           ──────────────────────────────────────────
30 Countries                             checkpoints/phase2_queue.txt
  × 15 Categories         ─────────→    (~175,000 unique app IDs)
  × 3 Chart Types                                  │
= 1,350 combinations                              ▼
         │                           ThreadPoolExecutor (10 workers)
         ▼                                         │
 PostgreSQL:                           For each app_id:
 country_charts table                  ├── Fetch 40 fields via Tor/proxy
         │                             ├── Filter: min_installs ≥ 100,000
         └── collect unique app_ids    ├── Upsert → PostgreSQL: apps
                                       └── For each of 30 countries:
                                           └── Insert → app_country_stats
                                                         │
                                                         ▼
                                       DuckDB reads PostgreSQL tables
                                       for fast 5-dimension analysis
```

---

## 📈 Expected Final Dataset

| Table | Rows | Est. Size |
|---|---|---|
| `apps` | ~175,000 | ~800 MB |
| `app_country_stats` | ~5,250,000 | ~2.5 GB |
| `country_charts` | ~810,000 | ~400 MB |
| **Total** | **~6.2M rows** | **~3.7 GB** |

---

## 🔢 Sample Analysis Queries

```sql
-- 1. Average rating by category
SELECT genre, ROUND(AVG(score)::numeric, 2) AS avg_rating, COUNT(*) AS apps
FROM apps GROUP BY genre ORDER BY avg_rating DESC;

-- 2. Top 20 apps by installs in India
SELECT a.title, s.min_installs
FROM apps a JOIN app_country_stats s ON a.app_id = s.app_id
WHERE s.country = 'in' ORDER BY s.min_installs DESC LIMIT 20;

-- 3. Apps in top 50 charts across the most countries (rising)
SELECT app_id, COUNT(DISTINCT country) AS country_count
FROM country_charts WHERE chart_rank <= 50
GROUP BY app_id ORDER BY country_count DESC LIMIT 20;

-- 4. Free vs paid monetization breakdown
SELECT free, ad_supported, in_app_purchases, COUNT(*) AS count
FROM apps GROUP BY 1,2,3 ORDER BY count DESC;

-- 5. Category popularity by country (country_charts)
SELECT country, category, COUNT(DISTINCT app_id) AS unique_apps
FROM country_charts GROUP BY country, category
ORDER BY country, unique_apps DESC;
```

---

## ✅ Pre-Coding Checklist

- [x] Windows laptop (not Pi)
- [x] Sleep settings disabled
- [x] DuckDB + PostgreSQL stack chosen
- [x] Tor setup automated
- [x] 30 proxies (3 Webshare accounts)
- [x] Full checkpoint/resume system designed
- [ ] **Provide Webshare proxy credentials (all 3 accounts)** ← only remaining item

---

*Last updated: 2026-05-04*
