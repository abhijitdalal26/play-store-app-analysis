# Google Play Store Tapive Dataset Analysis

Analysis of the **Tapive Google Play Store dataset** (~1.1 GB, ~2M+ apps, 36 columns).

## Files

| File | Purpose |
|------|---------|
| `google_play_store_kaggle_dataset_analysis.ipynb` | Main analysis notebook |
| `plot_helpers.py` | All chart functions (keeps notebook cells clean) |
| `images/` | Auto-generated chart PNGs (created on first run) |

## Architecture

```
Notebook cell                       plot_helpers.py
─────────────────────               ─────────────────────────────────
DuckDB query → DataFrame    ──►    ph.plot_xxx(dataframe)  →  chart
```

Every notebook cell does exactly two things:
1. **Query** the data with DuckDB SQL (fast, streams 1.1 GB CSV, no RAM pressure)
2. **Call** a `ph.plot_xxx()` function that renders the chart

## Sections

| # | Theme | Questions |
|---|-------|-----------|
| 1 | Data Overview | Schema, missing values, duplicate check |
| 2 | Descriptive | Distributions — ratings, installs, categories, reviews, release year, IAP price |
| 3 | Comparative | Free vs Paid, IAP effect, ad effect, monetization models |
| 4 | Correlational | Reviews↔Installs, age↔installs, screenshots, price sweet spot, heatmap |
| 5 | Outliers | Viral-but-bad apps, inflated ratings, oversaturated categories, dev quality |
| 6 | Developer Patterns | Prolific devs, single vs multi-app, quality vs quantity |
| 7 | Business Insights | Opportunity gap, top-app profile, monetization by tier |
| 8 | Key Takeaways | Summary findings |

## How to Run

```bash
# activate your venv first, then
pip install duckdb plotly kaleido nbformat pandas numpy matplotlib seaborn

# open notebook
jupyter lab google_play_store_kaggle_dataset_analysis.ipynb
```

> **For Kaggle upload**: change `DATA_PATH` in the Setup cell (Section 0) to:  
> `/kaggle/input/<your-dataset-slug>/google-play-dataset-by-tapivedotcom.csv`

## Column Reference

| Column | Meaning |
|--------|---------|
| `appId` | Unique package name — use to look up app in CSV or Play Store |
| `title` | App display name |
| `developer` / `developerId` | Developer name / numeric ID |
| `free` | 1=Free, 0=Paid |
| `price` | Price (USD) |
| `offersIAP` | 1=has in-app purchases |
| `minprice` / `maxprice` | IAP price range (only when offersIAP=1) |
| `adSupported` | 1=shows ads |
| `genre` / `genreId` | Category name / ID |
| `score` | Rating 0–5 |
| `ratings` | Total rating count |
| `reviews` | Total review count |
| `histogram1–5` | Star breakdown (1★ to 5★ vote counts) |
| `minInstalls` | Install count (floor bucket, e.g. 1000000) |
| `releasedYear/Month/Day` | Release date components |
| `ParseReleasedDayYear` | Parsed full release date |
| `dateUpdated` | Last update date string |
| `len screenshots` | Number of screenshots in Play Store listing |
