# Google Play Store App Analysis

![Google Play Store analysis banner](images/logo.png)

A streamlined, direct-connection data extraction pipeline for discovering and analyzing Google Play Store apps across 10 priority markets.

## Project Goal

Perform comprehensive market research to identify high-opportunity, low-competition app niches by:
1.  Analyzing a 3.46M historical dataset (Tapivedotcom baseline).
2.  Building a fresh 2026 dataset via local, direct-connection scraping.
3.  Comparing the historical baseline with a fresh 2026 sample to understand current market structure, monetization, regional demand, and opportunity signals.

## Focus Countries

```text
us, in, br, id, mx, gb, de, jp, kr, ph
```

## Setup

1.  **Install Dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    Create a `.env` file with your PostgreSQL credentials:
    ```env
    DB_USER=postgres
    DB_PASS=your_password
    DB_NAME=playstore
    DB_HOST=localhost
    DB_PORT=5433
    THREADS=8
    MIN_INSTALLS=0
    ```

3.  **Initialize Database:**
    ```powershell
    python -m extraction.setup_db
    ```

## Usage

### 1. Discovery
Build a queue of app IDs from charts, categories, and keyword searches:
```powershell
python -m extraction.discover_ids
```

### 2. Extraction
Download full metadata and multi-country stats for queued apps:
```powershell
python -m extraction.extract_details
```
*To test a small batch (e.g., 5 apps):*
```powershell
python -m extraction.extract_details 5
```

### 3. Monitoring
Check the current status of the scraping queue:
```powershell
python -m extraction.status
```

### 4. Analysis
Run a quick summary of the PostgreSQL database:
```powershell
python -m extraction.analyze
```

## Analysis Notebooks
The repository currently keeps two analysis workspaces:

- `google_play_store_analysis_2026/`: completed analysis for the fresh 2026 scrape of 11,176 unique apps across 10 markets.
- `google_play_store_analysis_tapivedotcom/`: separate workspace for the larger Tapive dataset analysis.

## Datasets

The raw CSV datasets are not committed to this repository because of their size. Download them from Kaggle if you want to reproduce the notebooks locally:

- **2026 scraped dataset (11,176 apps):** [Google Play Store App Dataset 2026](https://www.kaggle.com/datasets/abhijitdalal26/google-play-store-app-dataset-2026)
- **Tapive historical dataset (~3.46M app records):** [Google Play Apps and Games](https://www.kaggle.com/datasets/tapive/google-play-apps-and-games)

Place downloaded files under `data/` using the paths expected by the notebooks.

## Project Structure
- `extraction/`: Contains all scraper, discovery, database, and configuration code.
- `google_play_store_analysis_2026/`: Finished 2026 scraped-data notebook, reusable visualization code, and exported figures.
- `google_play_store_analysis_tapivedotcom/`: Larger historical Tapive dataset notebook and plotting helpers.
- `data/`: Local storage for the raw datasets (CSV) - git-ignored.
- `data_my_copy/scraped_2026/`: Enhanced Excel versions of the three 2026 data files (`apps.xlsx`, `app_country_stats.xlsx`, `discovery_signals.xlsx`). Each file includes a Dashboard sheet with summary stats and charts, auto-filters, frozen headers, and conditional formatting.
- `enhance_excel.py`: Script that (re-)generates the enhanced Excel files from the CSVs. Run `python enhance_excel.py` from the project root.
