# Google Play Store App Analysis

A streamlined, direct-connection data extraction pipeline for discovering and analyzing Google Play Store apps across 10 priority markets.

## Project Goal

Perform comprehensive market research to identify high-opportunity, low-competition app niches by:
1.  Analyzing a 3.45M historical dataset (Tapivedotcom baseline).
2.  Building a fresh 2026 dataset via local, direct-connection scraping.
3.  Performing a "Time Machine" analysis to track survival rates and growth trends over time.

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
A template notebook for custom analysis is available in [notebooks/latest_extracted_data_analysis.ipynb](file:///d:/Projects/play-store-analysis-github/notebooks/latest_extracted_data_analysis.ipynb).

## Project Structure
- `extraction/`: Contains all scraper, discovery, database, and configuration code.
- `notebooks/`: Directory containing Jupyter notebooks for data analysis.
- `data/`: Local storage for the raw datasets (CSV) - git-ignored.
