"""
reset_data.py - Delete the current scraped dataset from PostgreSQL.
Usage: python reset_data.py
"""
from db import DatabaseManager


if __name__ == "__main__":
    db = DatabaseManager()
    db.create_tables()
    db.reset_data()
    db.close()
