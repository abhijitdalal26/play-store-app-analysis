# Google Play Store App Extraction Pipeline

This directory contains the self-contained scraping, discovery, configuration, and database management pipeline for Google Play Store app analysis.

---

## Prerequisites

Before running any script, make sure:
1.  Your **PostgreSQL database** is running.
2.  A `.env` file exists in the **project root** containing database credentials:
    ```env
    DB_USER=postgres
    DB_PASS=your_password
    DB_NAME=playstore
    DB_HOST=localhost
    DB_PORT=5433
    THREADS=8
    MIN_INSTALLS=0
    ```
3.  Dependencies from `requirements.txt` are installed in your Python environment.

---

## File Structure & Descriptions

All files live flatly inside the `extraction/` directory:

| Script | Description |
| :--- | :--- |
| **`config.py`** | Central configuration file containing target markets, genres, search keywords, thread limits, timeouts, and connection parameters. |
| **`db.py`** | Database Manager module handling connections, table schemas, insertion of scraped data, and queue management. |
| **`setup_db.py`** | Initializes the PostgreSQL database and sets up the schemas. |
| **`discover_ids.py`** | Scrapes top charts and queries focus search terms to discover new App IDs and enqueue them as `pending`. |
| **`extract_details.py`** | Fetches detailed metadata (US baseline) and country-specific statistics (installs, ratings, prices) for queued apps. |
| **`status.py`** | Outputs progress statistics of the scraping queue and discovery tasks. |
| **`time_estimate.py`** | Estimates completion time for the queued apps and assesses rate-limiting/ban risks. |
| **`analyze.py`** | Runs quick database analytics to display table row counts, top apps by downloads, and genre averages. |

---

## How to Run the Pipeline

Always run the scripts from the **project root directory** using Python's module (`-m`) flag:

### 1. Database Initialization
Create the database and schema tables in PostgreSQL:
```powershell
python -m extraction.setup_db
```

### 2. Run App Discovery
Build a queue of app IDs from charts, category lists, and target keyword searches across your focus countries:
```powershell
python -m extraction.discover_ids
```

### 3. Extract Detailed App Metadata
Download full metadata and multi-country installer data for the queued apps:
```powershell
# Scrapes the entire queue:
python -m extraction.extract_details

# Scrapes a small test batch (e.g. 5 apps):
python -m extraction.extract_details 5
```

### 4. Monitor Progress
Check the number of completed, pending, or failed apps in the queue:
```powershell
python -m extraction.status
```

### 5. Check Database Statistics
Run quick queries to see the most downloaded apps, active genres, and table sizes:
```powershell
python -m extraction.analyze
```

---

## Customizing Scraping Targets

You can configure exactly which apps are discovered and extracted by editing configuration constants inside [extraction/config.py](file:///d:/Projects/play-store-analysis-github/extraction/config.py):

*   **`MARKET_COUNTRIES`**: Change the list of country codes (e.g. `["us", "in", "br"]`) to target localized stats from specific regions.
*   **`CATEGORIES`**: Adjust target categories (e.g. `["SOCIAL", "FINANCE", "TOOLS"]`) to limit chart scraping scopes.
*   **`GLOBAL_SEARCH_KEYWORDS` & `COUNTRY_SEARCH_KEYWORDS`**: Customize focus keywords (e.g., adding `"workout timer"` or `"AI receipt tracker"`) to discover niche-specific apps.
*   **`MIN_INSTALLS`**: Set a filter threshold (e.g., `100_000` or `0` for all) to automatically skip or keep low-traction apps.

