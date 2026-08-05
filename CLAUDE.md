# Play Store Analysis — Project Notes

## Datasets
- `data/google-play-dataset-by-tapivedotcom.csv/google-play-dataset-by-tapivedotcom.csv` — 2022
  archive, 3.45M rows, 36 columns. Large (1.1GB) — never load fully into pandas; query it
  through DuckDB (`read_csv_auto`) and only pull aggregated results into a DataFrame.
- `data/scraped_2026/apps.csv` — 2026 live scrape, 11,176 apps, 46 columns. Small, safe to load
  whole.
- `data/scraped_2026/discovery_signals.csv` — 75.8k rows: keyword/chart-rank discoverability
  signals per app per country (2026 only, no 2022 equivalent).
- `data/scraped_2026/app_country_stats.csv` — 111.3k rows: per-country score/price/installs for
  the same 11,176 apps across 10 storefronts (us, in, br, id, mx, gb, de, jp, kr, ph). Note:
  `min_installs`/`ratings` are near-identical across countries for a given app (global totals
  duplicated per row) — only `score` and `price` carry real per-country signal; `price` is in
  local currency with no currency column, so don't compare raw price across countries without
  a caveat.
- Genre/category taxonomies match almost exactly between the 2022 and 2026 datasets (same
  `genre` strings), which is what makes the old-vs-new comparison in `analysis/m02_evolution.py`
  and `analysis/m01_market.py` (category share shift) possible.

## Analysis pipeline (`analysis/`)
Script-based (no notebooks), one module per report section, orchestrated by `run_all.py` →
`build_report.py`. See `analysis/README.md` for the full breakdown. Key conventions:
- All data access goes through `analysis/data_prep.py`; every builder function is wrapped in
  `cached()`, which parquet-caches to `analysis/cache/`. Delete a specific `.parquet` there to
  force a rebuild of just that aggregate (e.g. after an upstream cleaning bug fix).
- Chart styling constants and `save_static()` / `save_interactive()` helpers live in
  `analysis/charts.py` — use them rather than styling matplotlib/plotly ad hoc, so every chart in
  the report reads as one visual system.
- Static (matplotlib) vs. interactive (Plotly) is a per-chart judgment call: use interactive when
  hovering for an exact value or identifying one of many overlapping series actually helps (dense
  scatters, bubble charts, Lorenz curves); static otherwise.
- The report (`report/index.html`) embeds interactive charts via `<iframe src="../analysis/interactive/*.html">`.
  Because of that, opening the report with a bare `file://` URL will fail to load the iframes in
  most browsers (local-file CORS) — always preview through `python -m http.server` and a
  `localhost` URL.

## Legacy notebook workspaces
`google_play_store_analysis_2026/`, `google_play_store_analysis_tapivedotcom/`, and
`app_opportunity_research/` are earlier notebook-based analyses kept for reference — not
maintained as part of the `analysis/` pipeline above.
