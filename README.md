# 📱 Google Play Store App Analysis

> A data pipeline to scrape, store, and analyze **6+ million rows** of Google Play Store data across **30 countries**, **15 categories**, and **175,000+ apps**.

---

## 🎯 Project Goals

Analyze the Google Play Store across 5 key dimensions:
1. 📈 **Download Trends**: How app download volumes shift over time.
2. 🌍 **Country-wise Popularity**: Which apps dominate in each country.
3. 🗂️ **Category Trends**: Top-performing genres and category growth.
4. 🚀 **Top Rising Apps**: Apps climbing charts across multiple markets.
5. 💰 **Revenue & Monetization**: Free vs paid, ad-supported, in-app purchases.

---

## 🗄️ Tech Stack

- **Scraping**: `google-play-scraper` (Python)
- **Database**: PostgreSQL (Storage) & DuckDB (Analytics Engine)
- **Proxies**: Webshare.io & Tor Network
- **Concurrency**: Python `ThreadPoolExecutor`

---

## 🚀 Setup & Usage

### 1. Requirements
- Python 3.9+
- PostgreSQL
- Tor Network installed

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
DB_USER=postgres
DB_PASS=your_password
DB_NAME=playstore
DB_HOST=localhost
DB_PORT=5432
WEBSHARE_PROXY=http://username:password@p.webshare.io:80
```

### 3. Run
```bash
pip install -r requirements.txt
python setup_db.py
python phase1_charts.py
python phase2_details.py
python analyze.py
```

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. Always respect the Google Play Store Terms of Service and scrape responsibly with rate limiting and delays.
