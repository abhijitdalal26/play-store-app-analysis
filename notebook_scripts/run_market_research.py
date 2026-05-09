"""
Run report-oriented market research across:
1. Historical Tapivedotcom Google Play CSV.
2. Fresh PostgreSQL scrape when available.

Outputs are written to analysis_outputs/ as report-ready CSV files plus a
Markdown summary.

Run:
    python notebook_scripts/run_market_research.py
"""

from __future__ import annotations

from datetime import datetime

import duckdb
import pandas as pd
import psycopg2

from market_common import ARCHETYPE_SQL, OUTPUT_DIR, csv_literal, ensure_output_dir, require_dataset
from core.config import DB_CONFIG


SUMMARY_PATH = OUTPUT_DIR / "market_research_summary.md"


def write_csv(df: pd.DataFrame, name: str) -> None:
    path = OUTPUT_DIR / name
    df.to_csv(path, index=False)
    print(f"[write] {path} ({len(df):,} rows)")


def query(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetchdf()


def pg_query(sql: str) -> pd.DataFrame:
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
    finally:
        conn.close()


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    rows = ["| " + " | ".join(df.columns) + " |", "| " + " | ".join(["---"] * len(df.columns)) + " |"]
    for _, row in df.iterrows():
        rows.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(rows)


def create_views(con: duckdb.DuckDBPyConnection) -> None:
    source = csv_literal(require_dataset())
    con.execute(f"""
        CREATE OR REPLACE VIEW historical_apps AS
        SELECT
            appId AS app_id,
            title,
            developer,
            genre,
            genreId AS genre_id,
            CAST(COALESCE(minInstalls, 0) AS BIGINT) AS installs,
            CAST(COALESCE(score, 0) AS DOUBLE) AS score,
            CAST(COALESCE(ratings, 0) AS BIGINT) AS ratings,
            CAST(COALESCE(reviews, 0) AS BIGINT) AS reviews,
            CAST(COALESCE(price, 0) AS DOUBLE) AS price,
            CAST(COALESCE(free, 1) AS INTEGER) AS free,
            CAST(COALESCE(adSupported, 0) AS INTEGER) AS ad_supported,
            CAST(COALESCE(offersIAP, 0) AS INTEGER) AS offers_iap,
            TRY_CAST(releasedYear AS INTEGER) AS released_year,
            TRY_CAST(dateUpdated AS TIMESTAMP) AS updated_at,
            lower(COALESCE(title, '') || ' ' || COALESCE(summary, '')) AS searchable_text
        FROM read_csv_auto('{source}', header=true, sample_size=200000, ignore_errors=true);

        CREATE OR REPLACE VIEW historical_apps_labelled AS
        SELECT *, {ARCHETYPE_SQL} AS app_archetype
        FROM historical_apps;
    """)


def run_historical(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    outputs["historical_overview"] = query(con, """
        SELECT
            COUNT(*) AS total_apps,
            COUNT(DISTINCT app_id) AS distinct_apps,
            SUM(CASE WHEN installs >= 100000 THEN 1 ELSE 0 END) AS apps_100k_plus,
            SUM(CASE WHEN installs >= 100000 AND score >= 4.0 THEN 1 ELSE 0 END) AS successful_apps,
            ROUND(100.0 * SUM(CASE WHEN installs >= 100000 AND score >= 4.0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
            ROUND(100.0 * SUM(CASE WHEN free = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS free_apps_pct,
            median(installs) AS median_installs
        FROM historical_apps_labelled;
    """)
    outputs["historical_market_structure_by_category"] = query(con, """
        SELECT
            genre, COUNT(*) AS apps, SUM(installs) AS total_installs,
            ROUND(100.0 * SUM(installs) / SUM(SUM(installs)) OVER (), 2) AS install_share_pct,
            median(installs) AS median_installs,
            SUM(CASE WHEN installs < 1000 THEN 1 ELSE 0 END) AS under_1k_apps,
            ROUND(100.0 * SUM(CASE WHEN installs < 1000 THEN 1 ELSE 0 END) / COUNT(*), 2) AS under_1k_pct
        FROM historical_apps_labelled
        WHERE genre IS NOT NULL
        GROUP BY genre
        HAVING COUNT(*) >= 1000
        ORDER BY total_installs DESC;
    """)
    outputs["historical_top_1_percent_install_capture"] = query(con, """
        WITH ranked AS (
            SELECT installs, NTILE(100) OVER (ORDER BY installs DESC) AS bucket
            FROM historical_apps_labelled
        )
        SELECT
            SUM(CASE WHEN bucket = 1 THEN installs ELSE 0 END) AS top_1_pct_installs,
            SUM(installs) AS all_installs,
            ROUND(100.0 * SUM(CASE WHEN bucket = 1 THEN installs ELSE 0 END) / SUM(installs), 2) AS top_1_pct_install_share,
            COUNT(CASE WHEN bucket = 1 THEN 1 END) AS top_1_pct_app_count,
            COUNT(*) AS all_app_count
        FROM ranked;
    """)
    outputs["historical_low_traction_buckets_by_category"] = query(con, """
        SELECT
            genre, COUNT(*) AS total_apps,
            SUM(CASE WHEN installs < 100 THEN 1 ELSE 0 END) AS apps_under_100,
            SUM(CASE WHEN installs >= 100 AND installs < 1000 THEN 1 ELSE 0 END) AS apps_100_to_999,
            SUM(CASE WHEN installs >= 1000 AND installs < 10000 THEN 1 ELSE 0 END) AS apps_1k_to_9999,
            SUM(CASE WHEN installs >= 10000 AND installs < 50000 THEN 1 ELSE 0 END) AS apps_10k_to_49999,
            SUM(CASE WHEN installs < 50000 THEN 1 ELSE 0 END) AS apps_under_50k,
            ROUND(100.0 * SUM(CASE WHEN installs < 50000 THEN 1 ELSE 0 END) / COUNT(*), 2) AS under_50k_pct,
            median(installs) AS median_installs
        FROM historical_apps_labelled
        WHERE genre IS NOT NULL
        GROUP BY genre
        HAVING COUNT(*) >= 1000
        ORDER BY under_50k_pct DESC;
    """)
    outputs["historical_opportunity_scores"] = query(con, """
        WITH cat AS (
            SELECT genre, COUNT(*) AS competition,
                   SUM(CASE WHEN installs >= 100000 AND score >= 4.0 THEN 1 ELSE 0 END) AS successful_apps,
                   100.0 * SUM(CASE WHEN installs >= 100000 AND score >= 4.0 THEN 1 ELSE 0 END) / COUNT(*) AS success_rate_pct,
                   median(installs) AS median_installs,
                   avg(log10(installs + 1)) AS avg_log_installs,
                   avg(CASE WHEN score > 0 THEN score ELSE NULL END) AS avg_rating
            FROM historical_apps_labelled
            WHERE genre IS NOT NULL
            GROUP BY genre
            HAVING COUNT(*) >= 5000
        ),
        scaled AS (
            SELECT *,
                   percent_rank() OVER (ORDER BY competition DESC) AS low_competition_score,
                   percent_rank() OVER (ORDER BY avg_log_installs ASC) AS demand_score,
                   percent_rank() OVER (ORDER BY avg_rating ASC) AS happiness_score,
                   percent_rank() OVER (ORDER BY success_rate_pct ASC) AS proof_score
            FROM cat
        )
        SELECT genre, competition, successful_apps, ROUND(success_rate_pct, 2) AS success_rate_pct,
               median_installs, ROUND(avg_rating, 3) AS avg_rating,
               ROUND(100 * (0.35 * proof_score + 0.30 * demand_score + 0.20 * low_competition_score + 0.15 * happiness_score), 2) AS opportunity_score
        FROM scaled
        ORDER BY opportunity_score DESC;
    """)
    outputs["historical_oversaturated_categories"] = query(con, """
        WITH cat AS (
            SELECT genre, COUNT(*) AS apps, median(installs) AS median_installs,
                   avg(log10(installs + 1)) AS avg_log_installs,
                   ROUND(100.0 * SUM(CASE WHEN installs < 1000 THEN 1 ELSE 0 END) / COUNT(*), 2) AS under_1k_pct,
                   ROUND(avg(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS avg_rating
            FROM historical_apps_labelled
            WHERE genre IS NOT NULL
            GROUP BY genre
            HAVING COUNT(*) >= 1000
        )
        SELECT *, ROUND(100 * (
            0.45 * percent_rank() OVER (ORDER BY apps ASC) +
            0.35 * percent_rank() OVER (ORDER BY avg_log_installs DESC) +
            0.20 * percent_rank() OVER (ORDER BY under_1k_pct ASC)
        ), 2) AS oversaturation_score
        FROM cat
        ORDER BY oversaturation_score DESC;
    """)
    outputs["historical_category_install_concentration"] = query(con, """
        WITH ranked AS (
            SELECT genre, installs,
                   ROW_NUMBER() OVER (PARTITION BY genre ORDER BY installs DESC) AS install_rank
            FROM historical_apps_labelled
            WHERE genre IS NOT NULL
        )
        SELECT genre, COUNT(*) AS apps, SUM(installs) AS total_installs,
               ROUND(100.0 * SUM(CASE WHEN install_rank = 1 THEN installs ELSE 0 END) / NULLIF(SUM(installs), 0), 2) AS top_1_share_pct,
               ROUND(100.0 * SUM(CASE WHEN install_rank <= 3 THEN installs ELSE 0 END) / NULLIF(SUM(installs), 0), 2) AS top_3_share_pct,
               ROUND(100.0 * SUM(CASE WHEN install_rank <= 10 THEN installs ELSE 0 END) / NULLIF(SUM(installs), 0), 2) AS top_10_share_pct
        FROM ranked
        GROUP BY genre
        HAVING COUNT(*) >= 1000
        ORDER BY top_3_share_pct DESC;
    """)
    outputs["historical_min_viable_rating_by_category"] = query(con, """
        SELECT genre, COUNT(*) AS apps,
               COUNT(CASE WHEN installs >= 100000 THEN 1 END) AS apps_100k_plus,
               ROUND(quantile_cont(CASE WHEN installs >= 100000 THEN score ELSE NULL END, 0.25), 3) AS rating_floor_p25_100k,
               ROUND(quantile_cont(CASE WHEN installs >= 1000000 THEN score ELSE NULL END, 0.25), 3) AS rating_floor_p25_1m,
               ROUND(avg(CASE WHEN installs >= 100000 THEN score ELSE NULL END), 3) AS avg_rating_100k_plus
        FROM historical_apps_labelled
        WHERE genre IS NOT NULL AND score > 0
        GROUP BY genre
        HAVING COUNT(CASE WHEN installs >= 100000 THEN 1 END) >= 100
        ORDER BY rating_floor_p25_100k DESC;
    """)
    outputs["historical_dead_under_50k_by_category"] = query(con, """
        WITH max_date AS (SELECT max(updated_at) AS latest_update FROM historical_apps_labelled WHERE updated_at IS NOT NULL),
        labelled AS (
            SELECT h.*, date_diff('day', updated_at, latest_update) AS days_since_update,
                   CASE WHEN installs < 1000 AND ratings < 10 AND (updated_at IS NULL OR updated_at < latest_update - INTERVAL 730 DAY) THEN 1 ELSE 0 END AS dead_strict_under_1k,
                   CASE WHEN installs < 50000 AND (updated_at IS NULL OR updated_at < latest_update - INTERVAL 730 DAY) THEN 1 ELSE 0 END AS stale_low_traction_under_50k
            FROM historical_apps_labelled h CROSS JOIN max_date
        )
        SELECT genre, COUNT(*) AS total_apps,
               SUM(CASE WHEN installs < 50000 THEN 1 ELSE 0 END) AS apps_under_50k,
               ROUND(100.0 * SUM(CASE WHEN installs < 50000 THEN 1 ELSE 0 END) / COUNT(*), 2) AS under_50k_pct,
               SUM(dead_strict_under_1k) AS dead_strict_under_1k,
               ROUND(100.0 * SUM(dead_strict_under_1k) / COUNT(*), 2) AS dead_strict_under_1k_pct,
               SUM(stale_low_traction_under_50k) AS stale_low_traction_under_50k,
               ROUND(100.0 * SUM(stale_low_traction_under_50k) / COUNT(*), 2) AS stale_low_traction_under_50k_pct
        FROM labelled
        WHERE genre IS NOT NULL
        GROUP BY genre
        HAVING COUNT(*) >= 1000
        ORDER BY stale_low_traction_under_50k DESC;
    """)
    outputs["historical_rejected_despite_downloads_by_category"] = query(con, """
        SELECT genre, COUNT(*) AS total_apps,
               SUM(CASE WHEN installs >= 50000 AND score > 0 AND score < 3.0 AND ratings >= 500 THEN 1 ELSE 0 END) AS hated_50k_plus_apps,
               ROUND(100.0 * SUM(CASE WHEN installs >= 50000 AND score > 0 AND score < 3.0 AND ratings >= 500 THEN 1 ELSE 0 END) / COUNT(*), 2) AS hated_50k_plus_pct_of_category,
               SUM(CASE WHEN installs >= 100000 AND score > 0 AND score < 3.0 AND ratings >= 500 THEN 1 ELSE 0 END) AS hated_100k_plus_apps,
               SUM(CASE WHEN installs >= 50000 AND score >= 3.0 AND score < 3.5 AND ratings >= 500 THEN 1 ELSE 0 END) AS disliked_50k_plus_apps
        FROM historical_apps_labelled
        WHERE genre IS NOT NULL
        GROUP BY genre
        HAVING COUNT(*) >= 1000
        ORDER BY hated_50k_plus_apps DESC;
    """)
    outputs["historical_archetype_success_failure"] = query(con, """
        WITH max_date AS (SELECT max(updated_at) AS latest_update FROM historical_apps_labelled WHERE updated_at IS NOT NULL),
        labelled AS (
            SELECT h.*,
                   CASE WHEN installs >= 100000 AND score >= 4.0 THEN 1 ELSE 0 END AS is_successful,
                   CASE WHEN installs < 1000 AND ratings < 10 AND (updated_at IS NULL OR updated_at < latest_update - INTERVAL 730 DAY) THEN 1 ELSE 0 END AS is_strict_dead,
                   CASE WHEN installs >= 50000 AND score > 0 AND score < 3.0 AND ratings >= 500 THEN 1 ELSE 0 END AS is_rejected
            FROM historical_apps_labelled h CROSS JOIN max_date
        )
        SELECT app_archetype, COUNT(*) AS total_apps,
               SUM(is_successful) AS successful_apps,
               ROUND(100.0 * SUM(is_successful) / COUNT(*), 2) AS success_rate_pct,
               SUM(is_strict_dead) AS strict_dead_apps,
               ROUND(100.0 * SUM(is_strict_dead) / COUNT(*), 2) AS strict_dead_rate_pct,
               SUM(is_rejected) AS downloaded_but_rejected_apps,
               median(installs) AS median_installs,
               ROUND(avg(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS avg_rating
        FROM labelled
        GROUP BY app_archetype
        HAVING COUNT(*) >= 1000
        ORDER BY successful_apps DESC;
    """)
    outputs["historical_rating_stability_by_traction"] = query(con, """
        SELECT CASE
                   WHEN ratings < 10 THEN '<10 ratings'
                   WHEN ratings < 100 THEN '10-99 ratings'
                   WHEN ratings < 1000 THEN '100-999 ratings'
                   WHEN ratings < 10000 THEN '1k-9.9k ratings'
                   WHEN ratings < 100000 THEN '10k-99k ratings'
                   ELSE '100k+ ratings'
               END AS rating_count_bucket,
               COUNT(*) AS apps,
               ROUND(avg(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS avg_rating,
               ROUND(stddev_samp(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS rating_stddev,
               median(installs) AS median_installs
        FROM historical_apps_labelled
        WHERE score > 0
        GROUP BY rating_count_bucket
        ORDER BY median_installs;
    """)
    outputs["historical_pricing_model"] = query(con, """
        SELECT CASE WHEN free = 1 THEN 'Free' ELSE 'Paid' END AS pricing_model,
               COUNT(*) AS apps,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS app_share_pct,
               median(installs) AS median_installs,
               SUM(CASE WHEN installs >= 100000 THEN 1 ELSE 0 END) AS apps_100k_plus,
               ROUND(100.0 * SUM(CASE WHEN installs >= 100000 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_100k_plus,
               ROUND(avg(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS avg_rating,
               ROUND(avg(price), 2) AS avg_price
        FROM historical_apps_labelled
        GROUP BY pricing_model
        ORDER BY apps DESC;
    """)
    outputs["historical_monetization_combo"] = query(con, """
        SELECT CASE
                   WHEN ad_supported = 1 AND offers_iap = 1 THEN 'Ads + IAP'
                   WHEN ad_supported = 1 THEN 'Ads only'
                   WHEN offers_iap = 1 THEN 'IAP only'
                   ELSE 'No ads / no IAP'
               END AS monetization_combo,
               COUNT(*) AS apps,
               median(installs) AS median_installs,
               ROUND(avg(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS avg_rating,
               ROUND(100.0 * SUM(CASE WHEN installs >= 100000 AND score >= 4.0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
        FROM historical_apps_labelled
        GROUP BY monetization_combo
        ORDER BY success_rate_pct DESC;
    """)
    outputs["historical_top_500_common_traits"] = query(con, """
        WITH top_apps AS (
            SELECT * FROM historical_apps_labelled ORDER BY installs DESC, ratings DESC LIMIT 500
        )
        SELECT COUNT(*) AS top_apps, COUNT(DISTINCT genre) AS categories_represented,
               median(installs) AS median_installs,
               ROUND(avg(CASE WHEN score > 0 THEN score ELSE NULL END), 3) AS avg_rating,
               ROUND(quantile_cont(CASE WHEN score > 0 THEN score ELSE NULL END, 0.25), 3) AS rating_p25,
               median(ratings) AS median_ratings,
               ROUND(avg(free) * 100, 2) AS free_pct,
               ROUND(avg(ad_supported) * 100, 2) AS ad_supported_pct,
               ROUND(avg(offers_iap) * 100, 2) AS offers_iap_pct
        FROM top_apps;
    """)
    return outputs


def run_current() -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    try:
        outputs["current_overview"] = pg_query("""
            SELECT
                (SELECT COUNT(*) FROM app_queue) AS queued_apps,
                (SELECT COUNT(*) FROM apps) AS saved_100k_plus_apps,
                (SELECT COUNT(*) FROM app_country_stats) AS country_stat_rows,
                (SELECT COUNT(*) FROM discovery_signals) AS discovery_signals;
        """)
        outputs["current_category_strength"] = pg_query("""
            SELECT genre, COUNT(*) AS apps,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY min_installs) AS median_installs,
                   AVG(score) AS avg_rating,
                   AVG(CASE WHEN free THEN 1 ELSE 0 END) * 100 AS free_pct,
                   AVG(CASE WHEN ad_supported THEN 1 ELSE 0 END) * 100 AS ad_supported_pct,
                   AVG(CASE WHEN in_app_purchases THEN 1 ELSE 0 END) * 100 AS iap_pct
            FROM apps
            WHERE genre IS NOT NULL
            GROUP BY genre
            HAVING COUNT(*) >= 20
            ORDER BY apps DESC;
        """)
        outputs["current_keyword_yield"] = pg_query("""
            SELECT ds.keyword, COUNT(DISTINCT ds.app_id) AS discovered_apps,
                   COUNT(DISTINCT a.app_id) AS saved_100k_plus_apps,
                   ROUND((100.0 * COUNT(DISTINCT a.app_id) / NULLIF(COUNT(DISTINCT ds.app_id), 0))::numeric, 2) AS saved_yield_pct,
                   AVG(a.score) AS avg_saved_rating,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.min_installs) AS median_saved_installs
            FROM discovery_signals ds
            LEFT JOIN apps a ON a.app_id = ds.app_id
            WHERE ds.source = 'search' AND ds.keyword IS NOT NULL
            GROUP BY ds.keyword
            HAVING COUNT(DISTINCT ds.app_id) >= 10
            ORDER BY saved_100k_plus_apps DESC
            LIMIT 100;
        """)
        outputs["current_country_opportunity_scores"] = pg_query("""
            WITH country_cat AS (
                SELECT acs.country, a.genre, COUNT(*) AS apps,
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY acs.min_installs) AS median_country_installs,
                       AVG(LN(acs.min_installs + 1) / LN(10)) AS avg_log_country_installs,
                       AVG(acs.score) AS avg_country_rating
                FROM app_country_stats acs
                JOIN apps a ON a.app_id = acs.app_id
                WHERE a.genre IS NOT NULL AND acs.min_installs IS NOT NULL AND acs.score IS NOT NULL
                GROUP BY acs.country, a.genre
                HAVING COUNT(*) >= 10
            )
            SELECT *,
                   ROUND((100 * (
                       0.45 * PERCENT_RANK() OVER (PARTITION BY country ORDER BY avg_log_country_installs ASC) +
                       0.35 * PERCENT_RANK() OVER (PARTITION BY country ORDER BY apps DESC) +
                       0.20 * PERCENT_RANK() OVER (PARTITION BY country ORDER BY avg_country_rating ASC)
                   ))::numeric, 2) AS country_opportunity_score
            FROM country_cat
            ORDER BY country, country_opportunity_score DESC;
        """)
    except Exception as exc:
        print(f"[warn] Skipping PostgreSQL current-data queries: {exc}")
    return outputs


def build_summary(outputs: dict[str, pd.DataFrame]) -> str:
    overview = outputs["historical_overview"].iloc[0]
    lines = [
        "# Market Research Summary",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Historical World View",
        f"- Total apps scanned: {int(overview.total_apps):,}",
        f"- Successful apps: {int(overview.successful_apps):,}",
        f"- Macro success rate: {float(overview.success_rate_pct):.2f}%",
        f"- Free app share: {float(overview.free_apps_pct):.2f}%",
        f"- Median installs: {int(overview.median_installs):,}",
        "",
        "## Top Historical Opportunity Categories",
        markdown_table(outputs["historical_opportunity_scores"].head(10)),
        "",
        "## App Archetype Success/Failure",
        markdown_table(outputs["historical_archetype_success_failure"].head(12)),
        "",
        "## Pricing Reality",
        markdown_table(outputs["historical_pricing_model"]),
        "",
        "## Monetization",
        markdown_table(outputs["historical_monetization_combo"]),
    ]
    if "current_category_strength" in outputs:
        lines.extend(["", "## Current 2026 Fresh Scrape Categories", markdown_table(outputs["current_category_strength"].head(10))])
    return "\n".join(lines) + "\n"


def main() -> None:
    ensure_output_dir()
    con = duckdb.connect(database=":memory:")
    create_views(con)
    outputs = run_historical(con)
    outputs.update(run_current())
    for name, df in outputs.items():
        write_csv(df, f"{name}.csv")
    SUMMARY_PATH.write_text(build_summary(outputs), encoding="utf-8")
    print(f"[write] {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
