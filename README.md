# 📱 Google Play Store App Analysis

> A distributed, large-scale data pipeline to scrape, store, and analyze **6+ million rows** of Google Play Store data across **30 countries**, **15 categories**, and **175,000+ apps** — running on a Windows laptop using a fully free, production-grade tech stack.

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
| **Fields per app** | 40 fields (full `google-play-scraper` output) |
| **Total rows** | ~6.2 million across 3 tables |
| **Storage** | ~3.7 GB (PostgreSQL) |

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
30 Countries                                checkpoints/phase2_queue.txt
  × 15 Categories           ──────→         (~175,000 unique app IDs)
  × 3 Chart Types                                     │
= 1,350 combinations                                  ▼
         │                               ThreadPoolExecutor (10 workers)
         ▼                                            │
  PostgreSQL:                              For each app_id:
  country_charts table                    ├── Fetch 40 fields via Tor/proxy
         │                                ├── Filter: min_installs ≥ 100K
         └── collect unique app_ids       ├── Upsert → apps table
                                          └── For each of 30 countries:
                                              └── Insert → app_country_stats
                                                            │
                                                            ▼
                                              DuckDB reads PostgreSQL
                                              for fast analytical queries
```

---

## 🗄️ Tech Stack

| Component | Tool | Why |
|---|---|---|
| **Primary Storage** | [PostgreSQL](https://www.postgresql.org/) | Industry-standard RDBMS. Connects to all BI tools. ACID-safe. |
| **Analytics Engine** | [DuckDB](https://duckdb.org/) | 10–50x faster than PostgreSQL for GROUP BY / window functions on millions of rows. |
| **Scraping Library** | [`google-play-scraper`](https://github.com/JoMingyu/google-play-scraper) | Python library interfacing with Play Store's internal API. |
| **Proxy (Phase 2)** | Tor Network via [`stem`](https://stem.torproject.org/) | Free, rotating residential-like IPs. Circuit renewed every 10 requests. |
| **Proxy (Phase 1)** | Webshare.io (30 free proxies across 3 accounts) | Fast datacenter proxies for lighter chart scraping. |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` | 10 parallel workers. |
| **Progress** | `tqdm` | Real-time progress bars with ETA. |

---

## 🔄 Proxy Strategy (100% Free)

| Source | Proxies | Role |
|---|---|---|
| **Webshare.io** (3 free accounts) | 30 datacenter proxies | Phase 1 primary + Phase 2 fallback |
| **Tor Network** | ∞ rotating | Phase 2 primary (renews IP every 10 requests) |
| **proxyscrape.com** | ~100–200 public | Last-resort fallback, refreshed hourly |

---

## ✅ Checkpoint & Resume System

The scraper is **fully resumable**. If your laptop crashes, loses internet, or you need to pause — **zero progress is lost.**

```
checkpoints/
├── phase1_done.txt      # Completed chart combinations
├── phase2_queue.txt     # All 175,000 app IDs (written once after Phase 1)
├── phase2_done.txt      # Completed app IDs
└── phase2_failed.txt    # Apps that failed all retries (logged and skipped)
```

Re-running the script automatically picks up from where it stopped:
```powershell
python phase2_details.py
# Resuming. 43,217 done. 131,783 remaining. Est. 38 hours left.
```

---

## 📁 Project Structure

```
play-store-analysis/
├── setup_tor.ps1           # Automated Tor download, install & configure
├── setup_db.py             # Creates PostgreSQL DB, tables, and indexes
├── config.py               # Countries, categories, proxy list, constants
├── db.py                   # PostgreSQL connection + upsert/insert methods
├── proxies.py              # 30 Webshare + Tor + proxyscrape rotation
├── checkpoint.py           # Crash-safe progress tracking
├── phase1_charts.py        # Phase 1: scrape top charts
├── phase2_details.py       # Phase 2: scrape full app details
├── analyze.py              # DuckDB analytics over PostgreSQL data
├── requirements.txt        # Python dependencies
├── IMPLEMENTATION_PLAN.md  # Full technical design document
└── checkpoints/            # Auto-created on first run
```

---

## 🚀 Setup & Usage

### 1. Install PostgreSQL
Download the Windows installer from [postgresql.org](https://www.postgresql.org/download/windows/). Run it, set a password, keep port `5432`.

### 2. Install Tor (Automated)
```powershell
.\setup_tor.ps1
```

### 3. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Create Database
```powershell
python setup_db.py
```

### 5. Add Proxy Credentials
Edit `config.py` → paste all 30 Webshare proxy credentials.

### 6. Run Phase 1
```powershell
python phase1_charts.py
```

### 7. Run Phase 2
```powershell
python phase2_details.py
```

### 8. Analyze
```powershell
python analyze.py
```

---

## 📈 Sample Analysis Queries

```sql
-- Average rating by category
SELECT genre, ROUND(AVG(score)::numeric, 2) AS avg_rating, COUNT(*) AS apps
FROM apps GROUP BY genre ORDER BY avg_rating DESC;

-- Top 20 apps by installs in India
SELECT a.title, s.min_installs
FROM apps a JOIN app_country_stats s ON a.app_id = s.app_id
WHERE s.country = 'in' ORDER BY s.min_installs DESC LIMIT 20;

-- Rising apps: top 50 charts in the most countries
SELECT app_id, COUNT(DISTINCT country) AS country_count
FROM country_charts WHERE chart_rank <= 50
GROUP BY app_id ORDER BY country_count DESC LIMIT 20;

-- Monetization breakdown
SELECT free, ad_supported, in_app_purchases, COUNT(*) AS count
FROM apps GROUP BY 1, 2, 3 ORDER BY count DESC;
```

---

## 📋 Status

> ⚙️ **In Development** — Implementation plan finalized. Awaiting proxy credentials to begin coding.

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) for full technical design.

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. Always respect [Google Play Store Terms of Service](https://play.google.com/intl/en_us/about/play-terms/) and scrape responsibly with rate limiting and delays.

---

## 📄 License

MIT License
