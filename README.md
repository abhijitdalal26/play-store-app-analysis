# Google Play Store App Analysis

![Google Play Store analysis banner](images/logo.png)

Project write-up: [abhijitdalal.vercel.app/projects/play-store-app-analysis](https://abhijitdalal.vercel.app/projects/play-store-app-analysis)

Full analysis report: [abhijitdalal26.github.io/play-store-app-analysis](https://abhijitdalal26.github.io/play-store-app-analysis/)

A streamlined, direct-connection data extraction pipeline for discovering and analyzing Google Play Store apps across 10 priority markets.

## Project Goal

Perform comprehensive market research to identify high-opportunity, low-competition app niches by:
1.  Analyzing a 3.46M historical dataset (Tapivedotcom baseline).
2.  Building a fresh 2026 dataset via local, direct-connection scraping.
3.  Comparing the historical baseline with a fresh 2026 sample to understand current market structure, monetization, regional demand, and opportunity signals.
4.  Translating findings into actionable app-build decisions across three strategies: original concepts, clone-and-improve, and direct clones.

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

## Analysis Report (`analysis/`)

A script-based (not notebook-based) analysis pipeline that produces a single
portfolio-quality HTML report, `report/index.html`, combining both datasets
into one narrative: market landscape, 2022→2026 evolution, ratings/quality,
monetization, developer concentration, freshness, geography &
discoverability, and an opportunity synthesis. Static charts (matplotlib) and
interactive charts (Plotly) are both used, picked per-chart based on whether
hovering for exact values adds anything.

Run it:
```powershell
python -m analysis.run_all
python -m http.server 8000   # then open http://localhost:8000/report/index.html
```

See `analysis/README.md` for the module layout and how to add a new section.

## Analysis Notebooks
The repository also keeps three earlier, notebook-based analysis workspaces:

### Exploratory analysis
- `google_play_store_analysis_2026/`: completed analysis for the fresh 2026 scrape of 11,176 unique apps across 10 markets.
- `google_play_store_analysis_tapivedotcom/`: separate workspace for the larger Tapive dataset analysis.

### App opportunity research (`app_opportunity_research/`)
Three-part analysis that cross-references both datasets to answer: **what should we build?**

Each notebook flags and separates big-tech apps (Google, Meta, Microsoft, Amazon, etc.) — they are kept for context/benchmarking but all opportunity rankings run on indie apps only, so results reflect realistic competition.

| Notebook | Question answered | Key outputs |
|---|---|---|
| `part1_original_app_ideas.ipynb` | Which **category** to build something new in? | Underserved categories, niche goldmines, 2026 growth signals, composite opportunity score |
| `part2_clone_and_improve.ipynb` | Which **specific apps** to clone and fix? | High-install / low-rating targets, abandoned apps (2+ years stale), weak category leaders |
| `part3_direct_clone.ipynb` | Which **proven formulas** to replicate directly? | Gold-standard indie apps (1M+ installs, 4.2+ rating), validated niches with 5+ winners, title keyword patterns |

**Charts generated per notebook:**
- Part 1: `p1_bigtech_context.png`, `p1_underserved_categories.png`, `p1_niche_goldmines.png`, `p1_growing_categories.png`, `p1_no_clear_winner.png`, `p1_final_recommendations.png`
- Part 2: `p2_bigtech_context.png`, `p2_clone_zone.png`, `p2_stale_apps.png`, `p2_weak_leaders.png`, `p2_final_summary.png`
- Part 3: `p3_gold_standard.png`, `p3_validated_formulas.png`, `p3_title_keywords.png`, `p3_final_recommendations.png`

## Datasets

The raw CSV datasets are not committed to this repository because of their size. Download them from Kaggle if you want to reproduce the notebooks locally:

- **2026 scraped dataset (11,176 apps):** [Google Play Store App Dataset 2026](https://www.kaggle.com/datasets/abhijitdalal26/google-play-store-app-dataset-2026)
- **Tapive historical dataset (~3.46M app records):** [Google Play Apps and Games](https://www.kaggle.com/datasets/tapive/google-play-apps-and-games)

Place downloaded files under `data/` using the paths expected by the notebooks.

## Project Structure
- `analysis/`: Script-based analysis pipeline (DuckDB-backed data prep, matplotlib/Plotly charts, HTML report generator). Outputs `report/index.html`.
- `extraction/`: Contains all scraper, discovery, database, and configuration code.
- `google_play_store_analysis_2026/`: Finished 2026 scraped-data notebook, reusable visualization code, and exported figures.
- `google_play_store_analysis_tapivedotcom/`: Larger historical Tapive dataset notebook and plotting helpers.
- `app_opportunity_research/`: Three-part opportunity research notebooks — what to build, what to clone-and-improve, what to clone directly. See [App opportunity research](#app-opportunity-research-app_opportunity_research) above.
- `data/`: Local storage for the raw datasets (CSV) - git-ignored.
- `data_my_copy/scraped_2026/`: Enhanced Excel versions of the three 2026 data files (`apps.xlsx`, `app_country_stats.xlsx`, `discovery_signals.xlsx`). Each file includes a Dashboard sheet with summary stats and charts, auto-filters, frozen headers, and conditional formatting.
- `enhance_excel.py`: Script that (re-)generates the enhanced Excel files from the CSVs. Run `python enhance_excel.py` from the project root.
