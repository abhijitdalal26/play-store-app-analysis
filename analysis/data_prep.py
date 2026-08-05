"""
Data access layer for the Play Store analysis.

All heavy lifting (filtering, grouping, joining) happens inside DuckDB so we
never have to pull the 3.45M-row 2022 CSV fully into pandas. Every builder
result is cached to analysis/cache/*.parquet so re-running the pipeline after
the first pass is fast.
"""
import duckdb
import pandas as pd
from pathlib import Path

from analysis import bigtech

ROOT = Path(__file__).resolve().parent.parent
OLD_CSV = ROOT / "data/google-play-dataset-by-tapivedotcom.csv/google-play-dataset-by-tapivedotcom.csv"
NEW_APPS = ROOT / "data/scraped_2026/apps.csv"
NEW_SIGNALS = ROOT / "data/scraped_2026/discovery_signals.csv"
NEW_COUNTRY = ROOT / "data/scraped_2026/app_country_stats.csv"

CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)


def _con():
    con = duckdb.connect()
    con.execute("PRAGMA threads=4")
    return con


def cached(name, builder):
    fp = CACHE / f"{name}.parquet"
    if fp.exists():
        return pd.read_parquet(fp)
    df = builder()
    df.to_parquet(fp)
    return df


# ──────────────────────────────────────────────────────────────────────────
# 2022 dataset (tapivedotcom, 3.45M apps) — everything aggregated in SQL
# ──────────────────────────────────────────────────────────────────────────

def old_headline_stats():
    def build():
        con = _con()
        q = f"""
        SELECT
            COUNT(*) AS n_apps,
            COUNT(DISTINCT developerId) AS n_developers,
            COUNT(DISTINCT genre) AS n_genres,
            AVG(free) AS pct_free,
            AVG(score) AS avg_score,
            MEDIAN(score) AS median_score,
            MEDIAN(minInstalls) AS median_installs,
            SUM(minInstalls) AS total_installs,
            AVG(containsAds) AS pct_ads,
            AVG(offersIAP) AS pct_iap,
            MIN(releasedYear) AS min_year,
            MAX(releasedYear) AS max_year
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        """
        return con.execute(q).df()
    return cached("old_headline", build)


def old_genre_stats():
    def build():
        con = _con()
        q = f"""
        WITH base AS (
            SELECT genre, minInstalls, score, free, containsAds, offersIAP, price
            FROM read_csv_auto('{OLD_CSV.as_posix()}')
            WHERE genre IS NOT NULL
        ),
        ranked AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY genre ORDER BY minInstalls DESC) AS rn,
                   SUM(minInstalls) OVER (PARTITION BY genre) AS genre_total
            FROM base
        ),
        cr3 AS (
            SELECT genre, SUM(minInstalls) / MAX(genre_total) AS cr3_share
            FROM ranked WHERE rn <= 3
            GROUP BY genre
        )
        SELECT
            b.genre,
            COUNT(*) AS app_count,
            MEDIAN(b.minInstalls) AS median_installs,
            SUM(b.minInstalls) AS total_installs,
            AVG(b.score) AS avg_score,
            AVG(b.free) AS pct_free,
            AVG(b.containsAds) AS pct_ads,
            AVG(b.offersIAP) AS pct_iap,
            AVG(CASE WHEN b.free = 0 THEN b.price END) AS avg_paid_price,
            cr3.cr3_share
        FROM base b JOIN cr3 USING(genre)
        GROUP BY b.genre, cr3.cr3_share
        ORDER BY app_count DESC
        """
        return con.execute(q).df()
    return cached("old_genre_stats", build)


def old_genre_stats_indie():
    """Same as old_genre_stats() but with big-tech / pre-installed developers excluded —
    this is the version every competition/opportunity metric should use."""
    def build():
        con = _con()
        excl = bigtech.sql_exclude_clause("developer")
        q = f"""
        WITH base AS (
            SELECT genre, minInstalls, score, free, containsAds, offersIAP, price
            FROM read_csv_auto('{OLD_CSV.as_posix()}')
            WHERE genre IS NOT NULL AND developer IS NOT NULL AND ({excl})
        ),
        ranked AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY genre ORDER BY minInstalls DESC) AS rn,
                   SUM(minInstalls) OVER (PARTITION BY genre) AS genre_total
            FROM base
        ),
        cr3 AS (
            SELECT genre, SUM(minInstalls) / MAX(genre_total) AS cr3_share
            FROM ranked WHERE rn <= 3
            GROUP BY genre
        )
        SELECT
            b.genre,
            COUNT(*) AS app_count,
            MEDIAN(b.minInstalls) AS median_installs,
            SUM(b.minInstalls) AS total_installs,
            AVG(b.score) AS avg_score,
            AVG(b.free) AS pct_free,
            AVG(b.containsAds) AS pct_ads,
            AVG(b.offersIAP) AS pct_iap,
            AVG(CASE WHEN b.free = 0 THEN b.price END) AS avg_paid_price,
            cr3.cr3_share
        FROM base b JOIN cr3 USING(genre)
        GROUP BY b.genre, cr3.cr3_share
        ORDER BY app_count DESC
        """
        return con.execute(q).df()
    return cached("old_genre_stats_indie", build)


def old_bigtech_share_by_genre():
    def build():
        con = _con()
        match = bigtech.sql_match_clause("developer")
        q = f"""
        SELECT genre,
               AVG(CASE WHEN {match} THEN 1 ELSE 0 END) * 100 AS pct_big_tech_apps,
               SUM(CASE WHEN {match} THEN minInstalls ELSE 0 END) * 100.0 / SUM(minInstalls) AS pct_big_tech_installs
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        WHERE genre IS NOT NULL
        GROUP BY genre
        ORDER BY pct_big_tech_installs DESC
        """
        return con.execute(q).df()
    return cached("old_bigtech_share", build)


def old_score_histogram():
    def build():
        con = _con()
        q = f"""
        SELECT ROUND(score * 10) / 10 AS score_bin, COUNT(*) AS n
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        WHERE score IS NOT NULL AND score > 0
        GROUP BY score_bin ORDER BY score_bin
        """
        return con.execute(q).df()
    return cached("old_score_hist", build)


def old_release_trend():
    def build():
        con = _con()
        q = f"""
        SELECT releasedYear AS year,
               COUNT(*) AS app_count,
               AVG(score) AS avg_score,
               AVG(free) AS pct_free,
               AVG(containsAds) AS pct_ads,
               AVG(offersIAP) AS pct_iap,
               MEDIAN(minInstalls) AS median_installs
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        WHERE releasedYear BETWEEN 2009 AND 2022
        GROUP BY releasedYear ORDER BY releasedYear
        """
        return con.execute(q).df()
    return cached("old_release_trend", build)


def old_developer_portfolio():
    def build():
        con = _con()
        q = f"""
        SELECT developerId, ANY_VALUE(developer) AS developer,
               COUNT(*) AS app_count,
               SUM(minInstalls) AS total_installs,
               AVG(score) AS avg_score
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        WHERE developerId IS NOT NULL
        GROUP BY developerId
        """
        return con.execute(q).df()
    return cached("old_dev_portfolio", build)


def old_developer_portfolio_indie():
    def build():
        con = _con()
        excl = bigtech.sql_exclude_clause("developer")
        q = f"""
        SELECT developerId, ANY_VALUE(developer) AS developer,
               COUNT(*) AS app_count,
               SUM(minInstalls) AS total_installs,
               AVG(score) AS avg_score
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        WHERE developerId IS NOT NULL AND ({excl})
        GROUP BY developerId
        """
        return con.execute(q).df()
    return cached("old_dev_portfolio_indie", build)


def old_price_distribution():
    def build():
        con = _con()
        q = f"""
        SELECT price
        FROM read_csv_auto('{OLD_CSV.as_posix()}')
        WHERE free = 0 AND price > 0 AND price < 100
        """
        return con.execute(q).df()
    return cached("old_price_dist", build)


def old_content_rating_proxy():
    """The 2022 dataset has no content_rating column; use genre as content proxy fallback."""
    return None


# ──────────────────────────────────────────────────────────────────────────
# 2026 dataset (fresh scrape, 11,176 apps) — small enough to load whole
# ──────────────────────────────────────────────────────────────────────────

def new_apps():
    def build():
        con = _con()
        q = f"""
        SELECT app_id, title, genre, categories, min_installs, score, ratings,
               reviews, price, free, currency, developer, developer_id,
               content_rating, ad_supported, contains_ads, in_app_purchases,
               size, updated, version
        FROM read_csv_auto('{NEW_APPS.as_posix()}')
        """
        df = con.execute(q).df()
        df["updated_dt"] = pd.to_datetime(df["updated"], unit="s", errors="coerce")
        df["updated_year"] = df["updated_dt"].dt.year
        df["is_big_tech"] = df["developer"].apply(bigtech.is_big_tech)
        return df
    return cached("new_apps", build)


def new_apps_indie():
    apps = new_apps()
    return apps[~apps["is_big_tech"]].copy()


def new_genre_stats():
    def build():
        return _genre_stats_from(new_apps())
    return cached("new_genre_stats", build)


def _genre_stats_from(apps):
    g = apps.groupby("genre")
    out = g.agg(
        app_count=("app_id", "count"),
        median_installs=("min_installs", "median"),
        total_installs=("min_installs", "sum"),
        avg_score=("score", "mean"),
        pct_free=("free", "mean"),
        pct_ads=("contains_ads", "mean"),
        pct_iap=("in_app_purchases", "mean"),
    ).reset_index()

    def cr3(sub):
        tot = sub["min_installs"].sum()
        top3 = sub.nlargest(3, "min_installs")["min_installs"].sum()
        return top3 / tot if tot else 0

    cr3_vals = apps.groupby("genre").apply(cr3, include_groups=False)
    out["cr3_share"] = out["genre"].map(cr3_vals)
    return out.sort_values("app_count", ascending=False)


def new_genre_stats_indie():
    def build():
        return _genre_stats_from(new_apps_indie())
    return cached("new_genre_stats_indie", build)


def new_bigtech_share_by_genre():
    def build():
        apps = new_apps()
        g = apps.groupby("genre")
        pct_apps = g["is_big_tech"].mean() * 100
        pct_installs = apps.groupby("genre").apply(
            lambda s: s.loc[s["is_big_tech"], "min_installs"].sum() / s["min_installs"].sum() * 100
            if s["min_installs"].sum() else 0,
            include_groups=False,
        )
        return pd.DataFrame({"pct_big_tech_apps": pct_apps, "pct_big_tech_installs": pct_installs}) \
            .reset_index().sort_values("pct_big_tech_installs", ascending=False)
    return cached("new_bigtech_share", build)


def new_developer_portfolio_indie():
    def build():
        apps = new_apps_indie()
        g = apps.groupby("developer_id").agg(
            developer=("developer", "first"),
            app_count=("app_id", "count"),
            total_installs=("min_installs", "sum"),
            avg_score=("score", "mean"),
        ).reset_index()
        return g
    return cached("new_dev_portfolio_indie", build)


def new_discovery_signals():
    def build():
        con = _con()
        q = f"SELECT * FROM read_csv_auto('{NEW_SIGNALS.as_posix()}')"
        return con.execute(q).df()
    return cached("new_signals", build)


def new_country_stats():
    def build():
        con = _con()
        q = f"""
        SELECT app_id, country, min_installs, score, ratings, reviews, price, free
        FROM read_csv_auto('{NEW_COUNTRY.as_posix()}')
        """
        return con.execute(q).df()
    return cached("new_country", build)


def new_developer_portfolio():
    def build():
        apps = new_apps()
        g = apps.groupby("developer_id").agg(
            developer=("developer", "first"),
            app_count=("app_id", "count"),
            total_installs=("min_installs", "sum"),
            avg_score=("score", "mean"),
        ).reset_index()
        return g
    return cached("new_dev_portfolio", build)


if __name__ == "__main__":
    print("Old headline:\n", old_headline_stats())
    print("New apps shape:", new_apps().shape)
