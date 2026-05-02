# 📱 Google Play Store App Analysis

> A distributed, large-scale data pipeline to scrape, store, and analyze **5+ million rows** of Google Play Store data across 30 countries, 15 categories, and 175,000+ apps — running 24/7 on a Raspberry Pi 4B.

---

## 🎯 Project Goals

Analyze the Google Play Store across 5 key dimensions:

| # | Dimension | Description |
|---|---|---|
| 1 | 📈 **Download Trends** | How app download volumes shift over time |
| 2 | 🌍 **Country-wise Popularity** | Which apps dominate in each country |
| 3 | 🗂️ **Category Trends** | Top-performing genres and category growth |
| 4 | 🚀 **Top Rising Apps** | Apps climbing charts across multiple markets |
| 5 | 💰 **Revenue & Monetization** | Free vs paid, ad-supported, in-app purchases |

---

## 📊 Dataset Overview

| Parameter | Value |
|---|---|
| **Target apps** | ~175,000 apps (100K+ installs only) |
| **Countries** | 30 countries covering 95% of Play Store activity |
| **Categories** | 15 categories |
| **Fields per app** | 40 fields (full google-play-scraper output) |
| **Total rows** | ~5.25 million (`apps × countries`) |
| **Storage** | ~3.7 GB (DuckDB) |

### 🌍 30 Countries

| Tier | Countries |
|---|---|
| **Tier 1 — Must Have** | 🇺🇸 US · 🇮🇳 IN · 🇧🇷 BR · 🇮🇩 ID · 🇷🇺 RU |
| **Tier 2 — Big Markets** | 🇩🇪 DE · 🇫🇷 FR · 🇬🇧 GB · 🇯🇵 JP · 🇰🇷 KR · 🇲🇽 MX · 🇹🇷 TR · 🇻🇳 VN · 🇹🇭 TH · 🇵🇭 PH |
| **Tier 3 — Emerging** | 🇳🇬 NG · 🇿🇦 ZA · 🇪🇬 EG · 🇵🇰 PK · 🇧🇩 BD · 🇦🇷 AR · 🇨🇴 CO · 🇸🇦 SA · 🇦🇪 AE |
| **Tier 4 — High Revenue** | 🇨🇦 CA · 🇦🇺 AU · 🇮🇹 IT · 🇪🇸 ES · 🇳🇱 NL · 🇵🇱 PL · 🇸🇪 SE |

### 🗂️ 15 Categories

```
SOCIAL · FINANCE · TOOLS · GAME · ENTERTAINMENT · SHOPPING · EDUCATION
HEALTH_AND_FITNESS · TRAVEL_AND_LOCAL · FOOD_AND_DRINK · PRODUCTIVITY
COMMUNICATION · MAPS_AND_NAVIGATION · MUSIC_AND_AUDIO · PHOTOGRAPHY
```

---

## 🏗️ Architecture

```
Phase 1 — Chart Discovery (3–5 hrs)         Phase 2 — App Detail Scrape (48–72 hrs)
──────────────────────────────────          ────────────────────────────────────────────
30 Countries                                phase2_queue.txt
  × 15 Categories           ──────→         (~175,000 unique app IDs)
  × 3 Chart Types                                     │
= 1,350 chart fetches                                 ▼
         │                               ThreadPoolExecutor (8 workers)
         ▼                                            │
  country_charts table                     For each app_id:
  (chart rank snapshots)                   ├── Fetch 40-field detail via proxy/Tor
         │                                 ├── Filter: min_installs ≥ 100,000
         └── collect unique app_ids        ├── Save → `apps` table
                                           └── For each of 30 countries:
                                               └── Save → `app_country_stats` table
```

---

## 🗄️ Database: DuckDB

**Why DuckDB?** It's an embedded analytical database — no server needed, runs on the Pi, and is 10–50× faster than SQLite for complex aggregations on millions of rows.

### Schema (3 Tables)

```
apps                    app_country_stats           country_charts
────────────────        ──────────────────          ──────────────────
app_id (PK)             app_id (PK)                 country (PK)
title                   country (PK)                category (PK)
description             scraped_at (PK)             chart_type (PK)
min_installs            installs                    chart_rank (PK)
score                   min_installs                app_id
ratings                 score                       scraped_at (PK)
reviews                 ratings
genre                   reviews
developer               price
ad_supported            free
in_app_purchases        scraped_at
... (40 fields total)
```

---

## 🔄 Proxy Strategy (100% Free)

| Source | Type | Role |
|---|---|---|
| **Webshare.io** (10 free proxies) | Datacenter | Phase 1 charts only |
| **Tor Network** | Residential-like | Phase 2 primary (rotates every 10 requests) |
| **proxyscrape.com** | Public pool | Fallback, refreshed hourly |

---

## 🛡️ Anti-Ban Measures

- ⏱️ Random delays: **2.5–7.0 seconds** between requests
- 🔄 IP rotation via **Tor circuit renewal** every 10 requests
- 🕵️ **Rotating User-Agent** headers (via `fake-useragent`)
- 📉 Conservative **8 threads** (not aggressive burst scraping)
- 🔁 **Exponential backoff** on 429/block: 10s → 30s → 60s → 120s → skip
- 💾 **Checkpoint saving** — resume from crash without restarting

---

## 📁 Project Structure

```
play-store-analysis/
├── config.py               # Countries, categories, constants
├── db.py                   # DuckDB schema + upsert methods
├── proxies.py              # Proxy pool (Webshare + proxyscrape + Tor)
├── checkpoint.py           # Resumable progress tracking
├── phase1_charts.py        # Phase 1: scrape top charts
├── phase2_details.py       # Phase 2: scrape full app details
├── requirements.txt        # Python dependencies
├── IMPLEMENTATION_PLAN.md  # Full technical design document
└── checkpoints/
    ├── phase1_done.txt
    ├── phase2_queue.txt
    └── phase2_done.txt
```

---

## 🚀 Setup & Usage

### Prerequisites

- Raspberry Pi 4B (4GB RAM) running Raspberry Pi OS 64-bit
- Python 3.9+
- Tor installed

### 1. Install Dependencies

```bash
sudo apt update && sudo apt install -y tor
pip3 install google-play-scraper duckdb requests stem fake-useragent
```

### 2. Configure Tor

```bash
# Add to /etc/tor/torrc:
echo "ControlPort 9051" | sudo tee -a /etc/tor/torrc
sudo systemctl restart tor
```

### 3. Configure Proxies

Edit `config.py` and add your [Webshare.io](https://webshare.io) free proxy credentials (sign up is free, no credit card needed).

### 4. Run Phase 1

```bash
nohup python3 phase1_charts.py > phase1.log 2>&1 &
tail -f phase1.log
```

### 5. Run Phase 2 (after Phase 1 completes)

```bash
nohup python3 phase2_details.py > phase2.log 2>&1 &
tail -f phase2.log
```

### Monitor Progress

```bash
# Apps scraped so far
wc -l checkpoints/phase2_done.txt

# Quick DB query
python3 -c "import duckdb; c = duckdb.connect('playstore.duckdb'); print(c.execute('SELECT COUNT(*) FROM apps').fetchone())"
```

---

## 📈 Sample Analysis Queries

```sql
-- Average rating by category
SELECT genre, ROUND(AVG(score), 2) AS avg_rating, COUNT(*) AS apps
FROM apps GROUP BY genre ORDER BY avg_rating DESC;

-- Top 20 apps by installs in India
SELECT a.title, s.min_installs
FROM apps a JOIN app_country_stats s ON a.app_id = s.app_id
WHERE s.country = 'in' ORDER BY s.min_installs DESC LIMIT 20;

-- Rising apps: appearing in top 50 charts across the most countries
SELECT app_id, COUNT(DISTINCT country) AS country_count
FROM country_charts WHERE chart_rank <= 50
GROUP BY app_id ORDER BY country_count DESC LIMIT 20;

-- Monetization breakdown
SELECT ad_supported, in_app_purchases, COUNT(*) AS count
FROM apps GROUP BY 1, 2 ORDER BY count DESC;
```

---

## 🧰 Tech Stack

| Component | Tool |
|---|---|
| Scraping | [`google-play-scraper`](https://github.com/JoMingyu/google-play-scraper) (Python) |
| Database | [DuckDB](https://duckdb.org/) |
| Proxy Rotation | Tor + Webshare.io + proxyscrape.com |
| Tor Control | [`stem`](https://stem.torproject.org/) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` |
| Hardware | Raspberry Pi 4B (4GB RAM, 32GB SD) |

---

## 📋 Status

> ⚙️ **In Planning/Development** — Scraping pipeline not yet deployed.

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) for the full technical design.

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. Always respect the [Google Play Store Terms of Service](https://play.google.com/intl/en_us/about/play-terms/) and scrape responsibly with rate limiting and delays.

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.
