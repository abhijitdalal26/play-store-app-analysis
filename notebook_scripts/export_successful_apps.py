"""
Export full historical rows for successful apps.

Success definition:
    minInstalls >= 100,000 and score >= 4.0

Run:
    python notebook_scripts/export_successful_apps.py
"""

from __future__ import annotations

import duckdb

from market_common import ARCHETYPE_SQL, OUTPUT_DIR, csv_literal, ensure_output_dir, require_dataset


OUTPUT_PATH = OUTPUT_DIR / "historical_successful_apps_full.csv"


def main() -> None:
    source = csv_literal(require_dataset())
    output = csv_literal(ensure_output_dir() / OUTPUT_PATH.name)
    con = duckdb.connect(database=":memory:")
    con.execute(f"""
        COPY (
            WITH src AS (
                SELECT
                    *,
                    lower(COALESCE(title, '') || ' ' || COALESCE(summary, '')) AS searchable_text
                FROM read_csv_auto('{source}', header=true, sample_size=200000, ignore_errors=true)
            )
            SELECT
                * EXCLUDE (searchable_text) RENAME (column00 AS source_row_id),
                {ARCHETYPE_SQL} AS app_archetype
            FROM src
            WHERE COALESCE(minInstalls, 0) >= 100000
              AND COALESCE(score, 0) >= 4.0
            ORDER BY minInstalls DESC, ratings DESC
        )
        TO '{output}'
        (HEADER, DELIMITER ',');
    """)
    count = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{output}', header=true)").fetchone()[0]
    print(f"[write] {OUTPUT_PATH} ({count:,} successful apps)")


if __name__ == "__main__":
    main()
