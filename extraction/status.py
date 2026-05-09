"""
status.py - Show current queue and saved-data counts.
Usage: python status.py
"""
import psycopg2
from core.config import DB_CONFIG


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for table in ("app_queue", "discovery_signals", "discovery_tasks", "apps", "app_country_stats"):
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                print(f"{table}: {cur.fetchone()[0]}")
            cur.execute("""
                SELECT status, COUNT(*)
                FROM app_queue
                GROUP BY status
                ORDER BY COUNT(*) DESC;
            """)
            rows = cur.fetchall()
            if rows:
                print("\nqueue_status:")
                for status, count in rows:
                    print(f"{status}: {count}")
            cur.execute("""
                SELECT status, COUNT(*)
                FROM discovery_tasks
                GROUP BY status
                ORDER BY COUNT(*) DESC;
            """)
            rows = cur.fetchall()
            if rows:
                print("\ndiscovery_task_status:")
                for status, count in rows:
                    print(f"{status}: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
