# Play Store Analysis Pipeline

A proper, senior-analyst-style pass over both datasets in this repo — the 2022
tapivedotcom archive (3.45M apps) and the 2026 first-party scrape (11k apps
across 10 country storefronts). Plain Python scripts, not notebooks: fast to
re-run, easy to diff, easy to extend.

## Run it

```
python -m analysis.run_all
```

This rebuilds every cached aggregate (first run only — DuckDB queries against
the 3.45M-row CSV are cached to `analysis/cache/*.parquet` so subsequent runs
are seconds, not minutes), regenerates every chart, and writes the final
report to `report/index.html`.

Open the report with a local server (plain `file://` won't load the
interactive Plotly iframes in most browsers due to CORS restrictions on local
files):

```
python -m http.server 8000
# then visit http://localhost:8000/report/index.html
```

## Structure

- `data_prep.py` — all data access. Every heavy aggregation runs inside
  DuckDB directly against the CSVs so the 3.45M-row 2022 file is never fully
  materialized in pandas; only the aggregated results are cached.
- `charts.py` — shared palette, typography, and `save_static()` /
  `save_interactive()` helpers so every chart in the report looks like part
  of one system.
- `m01`–`m08` — one module per section of the story (market landscape,
  2022→2026 evolution, ratings & quality, monetization, developer
  concentration, freshness, geography & discoverability, opportunity
  synthesis). Each exposes a `build()` that returns section dicts (kicker,
  title, narrative, figures).
- `build_report.py` — assembles every section into `report/index.html`.
  Static charts are PNGs embedded directly; interactive charts are
  self-contained Plotly HTML fragments loaded via `<iframe>`.

## Adding a new section

Copy the shape of any `mNN_*.py` module: pull data from `data_prep`, save
charts through `charts.save_static` / `charts.save_interactive`, return a
list with one dict per section (`id`, `kicker`, `title`, `narrative`,
`figures`). Register the module's `build()` call in `build_report.build()`.
