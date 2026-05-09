"""
Export successful apps that look plausibly buildable by one person today with AI tools.

Inputs:
    analysis_outputs/historical_successful_apps_full.csv

Outputs:
    analysis_outputs/solo_buildable_successful_apps.csv
    analysis_outputs/solo_buildable_success_summary.csv
"""

from __future__ import annotations

import duckdb

from market_common import OUTPUT_DIR, csv_literal, ensure_output_dir


SUCCESSFUL_APPS_PATH = OUTPUT_DIR / "historical_successful_apps_full.csv"
OUTPUT_PATH = OUTPUT_DIR / "solo_buildable_successful_apps.csv"
SUMMARY_PATH = OUTPUT_DIR / "solo_buildable_success_summary.csv"


def main() -> None:
    ensure_output_dir()
    if not SUCCESSFUL_APPS_PATH.exists():
        raise FileNotFoundError("Run notebook_scripts/export_successful_apps.py first.")

    source = csv_literal(SUCCESSFUL_APPS_PATH)
    output = csv_literal(OUTPUT_PATH)
    summary = csv_literal(SUMMARY_PATH)
    con = duckdb.connect(database=":memory:")
    con.execute(f"""
        CREATE OR REPLACE VIEW successful_apps AS
        SELECT
            *,
            lower(COALESCE(title, '') || ' ' || COALESCE(summary, '') || ' ' || COALESCE(developer, '')) AS search_text
        FROM read_csv_auto('{source}', header=true, sample_size=200000, ignore_errors=true);
    """)
    con.execute("""
        CREATE OR REPLACE VIEW solo_ranked AS
        SELECT
            *,
            CASE
                WHEN genre IN ('Puzzle','Word','Trivia','Board','Card','Casual') THEN 'Simple repeatable game'
                WHEN regexp_matches(search_text, '(habit|water reminder|period tracker|period calendar|pregnancy|baby tracker|workout|calorie|diet|meditation|sleep|medicine reminder)') THEN 'Health/routine tracker'
                WHEN regexp_matches(search_text, '(qr|barcode)') THEN 'QR/barcode scanner'
                WHEN regexp_matches(search_text, '(pdf|scanner|ocr|document|compress|converter)') THEN 'PDF/document/scanner utility'
                WHEN genre NOT IN ('Action','Adventure','Arcade','Board','Card','Casino','Casual','Educational','Music','Puzzle','Racing','Role Playing','Simulation','Sports','Strategy','Trivia','Word')
                 AND regexp_matches(search_text, '(calculator|unit converter|bmi calculator|emi calculator|loan calculator|age calculator|tip calculator|tax calculator)') THEN 'Calculator/converter'
                WHEN regexp_matches(search_text, '(resume|cv|cover letter|interview|job tracker)') THEN 'Resume/job helper'
                WHEN regexp_matches(search_text, '(flashcard|quiz|exam|test prep|study|notes|learn english|grammar|dictionary|translator|pronunciation)') THEN 'Education/language micro-tool'
                WHEN regexp_matches(search_text, '(bible|quran|prayer|devotional|mantra|astrology|horoscope|calendar|festival)') THEN 'Religion/astrology/calendar'
                WHEN regexp_matches(search_text, '(weather|forecast|radar)') THEN 'Weather/local alert app'
                WHEN regexp_matches(search_text, '(wallpaper|theme|icon pack|font|emoji|sticker|keyboard)') THEN 'Personalization pack/tool'
                WHEN regexp_matches(search_text, '(photo editor|collage|filter|background remover|image resizer|photo frame|poster maker|logo maker|meme maker|caption|hashtag)') THEN 'Photo/design micro-tool'
                WHEN regexp_matches(search_text, '(video editor|slideshow|screen recorder|video maker)') THEN 'Video micro-tool'
                WHEN regexp_matches(search_text, '(expense|budget|money manager|bill reminder|subscription|receipt|invoice)') THEN 'Personal finance helper'
                ELSE NULL
            END AS solo_app_type,
            CASE
                WHEN regexp_matches(search_text, '(bank|banking|upi|wallet|payment|paytm|phonepe|google pay|paypal|crypto exchange|insurance|loan app|credit card)') THEN 1
                WHEN regexp_matches(search_text, '(facebook|instagram|whatsapp|messenger|twitter|snapchat|tiktok|youtube|netflix|spotify|amazon|google|microsoft|adobe|samsung|xiaomi|huawei|uber|lyft|booking|airbnb)') THEN 1
                WHEN regexp_matches(search_text, '(browser|antivirus|vpn|security|cleaner|booster|file manager|launcher)') THEN 1
                WHEN genre IN ('Communication','Social','Shopping','Maps & Navigation','Travel & Local') THEN 1
                ELSE 0
            END AS platform_or_trust_heavy_flag
        FROM successful_apps;
    """)
    con.execute("""
        CREATE OR REPLACE VIEW scored AS
        SELECT
            *,
            CASE
                WHEN solo_app_type IN ('QR/barcode scanner','Calculator/converter','Resume/job helper','Religion/astrology/calendar','Personalization pack/tool') THEN 90
                WHEN solo_app_type IN ('PDF/document/scanner utility','Education/language micro-tool','Health/routine tracker','Photo/design micro-tool','Personal finance helper') THEN 80
                WHEN solo_app_type IN ('Weather/local alert app','Video micro-tool','Simple repeatable game') THEN 70
                ELSE 0
            END
            - CASE WHEN platform_or_trust_heavy_flag = 1 THEN 35 ELSE 0 END
            - CASE WHEN minInstalls >= 1000000000 THEN 15 ELSE 0 END
            AS solo_buildability_score,
            CASE
                WHEN platform_or_trust_heavy_flag = 1 THEN 'Lower confidence: platform, trust-heavy, infrastructure, marketplace, social network, bank/payment, browser/security, or major brand dependency.'
                WHEN solo_app_type IS NOT NULL THEN 'Focused app pattern plausibly buildable today with AI-assisted coding, APIs, templates, and content generation.'
                ELSE 'No solo-buildable pattern matched.'
            END AS solo_buildability_reason
        FROM solo_ranked;
    """)
    con.execute(f"""
        COPY (
            SELECT
                solo_app_type, solo_buildability_score, solo_buildability_reason,
                source_row_id, appId, title, developer, developerId, developerWebsite,
                free, genre, genreId, app_archetype, minInstalls, score, ratings, reviews,
                price, offersIAP, adSupported, containsAds, summary, releasedDayYear,
                releasedYear, dateUpdated, histogram1, histogram2, histogram3, histogram4, histogram5
            FROM scored
            WHERE solo_app_type IS NOT NULL AND solo_buildability_score >= 60
            ORDER BY solo_buildability_score DESC, solo_app_type, minInstalls DESC, ratings DESC
        ) TO '{output}' (HEADER, DELIMITER ',');
    """)
    con.execute(f"""
        COPY (
            SELECT
                solo_app_type,
                COUNT(*) AS apps,
                median(minInstalls) AS median_installs,
                max(minInstalls) AS max_installs,
                ROUND(avg(score), 3) AS avg_rating,
                median(ratings) AS median_ratings,
                ROUND(avg(COALESCE(free, 1)) * 100, 2) AS free_pct,
                ROUND(avg(COALESCE(adSupported, 0)) * 100, 2) AS ad_supported_pct,
                ROUND(avg(COALESCE(offersIAP, 0)) * 100, 2) AS offers_iap_pct,
                ROUND(avg(solo_buildability_score), 2) AS avg_buildability_score
            FROM scored
            WHERE solo_app_type IS NOT NULL AND solo_buildability_score >= 60
            GROUP BY solo_app_type
            ORDER BY apps DESC, avg_buildability_score DESC
        ) TO '{summary}' (HEADER, DELIMITER ',');
    """)
    rows = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{output}', header=true)").fetchone()[0]
    print(f"[write] {OUTPUT_PATH} ({rows:,} apps)")
    print(f"[write] {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
