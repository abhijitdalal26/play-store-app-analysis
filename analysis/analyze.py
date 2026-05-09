"""
analyze.py - Quick PostgreSQL summary for the app dataset.
Usage: python analyze.py
"""
import psycopg2
from core.config import DB_CONFIG


def show(cur, title, query):
    print(f"\n## {title}")
    cur.execute(query)
    rows = cur.fetchall()
    if not rows:
        print("No rows yet.")
        return
    columns = [desc[0] for desc in cur.description]
    print(" | ".join(columns))
    print("-" * 100)
    for row in rows:
        print(" | ".join("" if val is None else str(val) for val in row))


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            show(cur, "Table Counts", """
                SELECT 'app_queue' AS table_name, COUNT(*) AS rows FROM app_queue
                UNION ALL SELECT 'discovery_signals', COUNT(*) FROM discovery_signals
                UNION ALL SELECT 'discovery_tasks', COUNT(*) FROM discovery_tasks
                UNION ALL SELECT 'apps_100k_plus', COUNT(*) FROM apps
                UNION ALL SELECT 'app_country_stats', COUNT(*) FROM app_country_stats;
            """)
            show(cur, "Queue Status", """
                SELECT status, COUNT(*) AS apps
                FROM app_queue
                GROUP BY status
                ORDER BY apps DESC;
            """)
            show(cur, "Top Saved Apps", """
                SELECT app_id, title, genre, min_installs, score, ratings
                FROM apps
                ORDER BY min_installs DESC NULLS LAST, ratings DESC NULLS LAST
                LIMIT 25;
            """)
            show(cur, "Genres", """
                SELECT genre, COUNT(*) AS apps, AVG(score) AS avg_score
                FROM apps
                GROUP BY genre
                ORDER BY apps DESC, genre
                LIMIT 25;
            """)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
