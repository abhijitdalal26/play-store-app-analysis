"""
Group successful apps into repeatable success patterns.

Input:
    analysis_outputs/historical_successful_apps_full.csv

Outputs:
    analysis_outputs/success_pattern_apps_full.csv
    analysis_outputs/success_pattern_summary.csv

An app can appear in multiple patterns.
"""

from __future__ import annotations

import duckdb

from market_common import GAME_GENRES, OUTPUT_DIR, csv_literal, ensure_output_dir


SUCCESSFUL_APPS_PATH = OUTPUT_DIR / "historical_successful_apps_full.csv"
PATTERN_APPS_PATH = OUTPUT_DIR / "success_pattern_apps_full.csv"
PATTERN_SUMMARY_PATH = OUTPUT_DIR / "success_pattern_summary.csv"


def main() -> None:
    ensure_output_dir()
    if not SUCCESSFUL_APPS_PATH.exists():
        raise FileNotFoundError("Run notebook_scripts/export_successful_apps.py first.")

    source = csv_literal(SUCCESSFUL_APPS_PATH)
    pattern_apps = csv_literal(PATTERN_APPS_PATH)
    pattern_summary = csv_literal(PATTERN_SUMMARY_PATH)
    con = duckdb.connect(database=":memory:")
    con.execute(f"""
        CREATE OR REPLACE VIEW successful_apps AS
        SELECT * FROM read_csv_auto('{source}', header=true, sample_size=200000, ignore_errors=true);
    """)
    con.execute(f"""
        CREATE OR REPLACE VIEW pattern_memberships_base AS
        SELECT
            'Engagement-loop games' AS success_pattern,
            CASE
                WHEN genre IN ('Casino','Card') THEN 'Casino/card chance and collection loops'
                WHEN genre IN ('Role Playing','Strategy','Simulation') THEN 'Progression, upgrades, characters, worlds'
                WHEN genre IN ('Puzzle','Word','Trivia','Board') THEN 'Repeatable short-session puzzle loops'
                WHEN genre IN ('Action','Adventure','Arcade','Racing','Sports','Casual') THEN 'Fast replay and skill/reward loops'
                ELSE 'Game engagement loop'
            END AS success_subpattern,
            'Repeat sessions, progression, collection, competition, cosmetics, or rewards.' AS pattern_reason,
            *
        FROM successful_apps
        WHERE genre IN ({GAME_GENRES})

        UNION ALL
        SELECT
            'Daily-pain utilities',
            CASE
                WHEN app_archetype = 'Weather apps' THEN 'Daily weather/forecast habit'
                WHEN app_archetype = 'Photo/video creation tools' THEN 'Frequent creation/editing need'
                WHEN app_archetype = 'Scanner/PDF/QR utilities' THEN 'Document/scanning workflow'
                WHEN app_archetype = 'Phone maintenance/security/browser tools' THEN 'Device/browser/file/security workflow'
                WHEN app_archetype = 'Finance and money tools' THEN 'Money/payment/budget workflow'
                WHEN app_archetype = 'Travel, maps, transport' THEN 'Navigation/transport workflow'
                WHEN app_archetype = 'Language learning/translation' THEN 'Repeated learning/translation habit'
                WHEN app_archetype = 'Health, fitness, wellness' THEN 'Routine health/fitness tracking'
                ELSE 'High-frequency utility'
            END,
            'Recurring pain point that creates repeat opening.',
            *
        FROM successful_apps
        WHERE app_archetype IN (
            'Weather apps','Photo/video creation tools','Scanner/PDF/QR utilities',
            'Phone maintenance/security/browser tools','Finance and money tools',
            'Travel, maps, transport','Language learning/translation','Health, fitness, wellness'
        )

        UNION ALL
        SELECT
            'Dual monetization winners',
            'Ads + IAP',
            'Reached success while supporting both ads and in-app purchases.',
            *
        FROM successful_apps
        WHERE COALESCE(adSupported, 0) = 1 AND COALESCE(offersIAP, 0) = 1

        UNION ALL
        SELECT
            'Free distribution winners',
            CASE
                WHEN minInstalls >= 100000000 THEN 'Massive free reach: 100M+ installs'
                WHEN minInstalls >= 10000000 THEN 'Large free reach: 10M+ installs'
                WHEN minInstalls >= 1000000 THEN 'Scaled free reach: 1M+ installs'
                ELSE 'Free app with 100k+ installs'
            END,
            'Free download removes adoption friction.',
            *
        FROM successful_apps
        WHERE COALESCE(free, 1) = 1

        UNION ALL
        SELECT
            'Personal expression and identity',
            CASE
                WHEN app_archetype = 'Personalization: wallpapers/themes/launchers' THEN 'Wallpapers/themes/launchers'
                WHEN app_archetype = 'Keyboard/font/emoji utilities' THEN 'Keyboard/font/emoji identity'
                WHEN app_archetype = 'Photo/video creation tools' THEN 'Creative self-expression'
                ELSE 'Personal expression'
            END,
            'Customization, style, communication, or shareable media.',
            *
        FROM successful_apps
        WHERE app_archetype IN (
            'Personalization: wallpapers/themes/launchers',
            'Keyboard/font/emoji utilities',
            'Photo/video creation tools'
        )

        UNION ALL
        SELECT
            'Localized trust and culture',
            CASE
                WHEN app_archetype = 'Religion/astrology/calendar' THEN 'Religion, astrology, calendar, devotional habit'
                WHEN app_archetype = 'Finance and money tools' THEN 'Local finance/payment trust'
                WHEN app_archetype = 'Language learning/translation' THEN 'Language/local learning need'
                ELSE 'Localized/cultural utility'
            END,
            'Matches local language, culture, payments, rituals, or trusted institutions.',
            *
        FROM successful_apps
        WHERE app_archetype IN ('Religion/astrology/calendar','Finance and money tools','Language learning/translation')

        UNION ALL
        SELECT
            'Frustrated-demand winners',
            app_archetype,
            'Category has success plus many high-install low-rating alternatives.',
            *
        FROM successful_apps
        WHERE app_archetype IN (
            'Finance and money tools','Photo/video creation tools','Scanner/PDF/QR utilities',
            'Phone maintenance/security/browser tools','Social, chat, dating','Travel, maps, transport'
        );
    """)
    con.execute("""
        CREATE OR REPLACE VIEW pattern_memberships AS
        SELECT * FROM pattern_memberships_base
        UNION ALL
        SELECT
            'Other successful apps',
            CASE WHEN COALESCE(free, 1) = 0 THEN 'Paid successful exception' ELSE 'Unclassified successful app' END,
            'Meets success definition but does not match current pattern rules.',
            *
        FROM successful_apps
        WHERE appId NOT IN (SELECT DISTINCT appId FROM pattern_memberships_base);
    """)
    con.execute(f"""
        COPY (
            SELECT * FROM pattern_memberships
            ORDER BY success_pattern, success_subpattern, minInstalls DESC, ratings DESC
        ) TO '{pattern_apps}' (HEADER, DELIMITER ',');
    """)
    con.execute(f"""
        COPY (
            SELECT
                success_pattern, success_subpattern, app_archetype, genre,
                COUNT(*) AS apps,
                median(minInstalls) AS median_installs,
                max(minInstalls) AS max_installs,
                ROUND(avg(score), 3) AS avg_rating,
                median(ratings) AS median_ratings,
                ROUND(avg(COALESCE(adSupported, 0)) * 100, 2) AS ad_supported_pct,
                ROUND(avg(COALESCE(offersIAP, 0)) * 100, 2) AS offers_iap_pct,
                ROUND(avg(COALESCE(free, 1)) * 100, 2) AS free_pct
            FROM pattern_memberships
            GROUP BY success_pattern, success_subpattern, app_archetype, genre
            ORDER BY success_pattern, apps DESC
        ) TO '{pattern_summary}' (HEADER, DELIMITER ',');
    """)
    rows = con.execute("SELECT COUNT(*) FROM pattern_memberships").fetchone()[0]
    unique_apps = con.execute("SELECT COUNT(DISTINCT appId) FROM pattern_memberships").fetchone()[0]
    print(f"[write] {PATTERN_APPS_PATH} ({rows:,} rows, {unique_apps:,} unique apps)")
    print(f"[write] {PATTERN_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
