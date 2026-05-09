"""
setup_db.py - Create the PostgreSQL database and project tables.
Usage: python setup_db.py
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from core.config import DB_CONFIG
from core.db import DatabaseManager


def create_database():
    cfg = {**DB_CONFIG, "dbname": "postgres"}
    conn = psycopg2.connect(**cfg)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    target = DB_CONFIG["dbname"]
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (target,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{target}";')
            print(f"[Setup] Database '{target}' created.")
        else:
            print(f"[Setup] Database '{target}' already exists.")
    conn.close()


if __name__ == "__main__":
    create_database()
    db = DatabaseManager()
    db.create_tables()
    db.close()
    print("[Setup] Done.")
