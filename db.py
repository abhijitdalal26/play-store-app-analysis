import json
import threading
import psycopg2
from psycopg2 import pool
from config import DB_CONFIG


class DatabaseManager:
    def __init__(self):
        self._pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=15, **DB_CONFIG)
        self._lock = threading.Lock()

    def close(self):
        self._pool.closeall()

    def _get_conn(self):
        return self._pool.getconn()

    def _put_conn(self, conn):
        self._pool.putconn(conn)

    def create_tables(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_queue (
                        app_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL DEFAULT 'pending',
                        min_installs BIGINT,
                        source_count INTEGER NOT NULL DEFAULT 0,
                        first_discovered_at TIMESTAMPTZ DEFAULT NOW(),
                        last_discovered_at TIMESTAMPTZ DEFAULT NOW(),
                        processed_at TIMESTAMPTZ,
                        last_error TEXT
                    );

                    CREATE TABLE IF NOT EXISTS discovery_signals (
                        id BIGSERIAL PRIMARY KEY,
                        app_id TEXT NOT NULL REFERENCES app_queue(app_id) ON DELETE CASCADE,
                        source TEXT NOT NULL,
                        country CHAR(2),
                        category TEXT,
                        keyword TEXT,
                        collection TEXT,
                        chart_rank INTEGER,
                        signal_key TEXT NOT NULL,
                        discovered_at TIMESTAMPTZ DEFAULT NOW(),
                        UNIQUE (signal_key)
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS apps (
                        app_id TEXT PRIMARY KEY,
                        title TEXT,
                        description TEXT,
                        summary TEXT,
                        installs TEXT,
                        min_installs BIGINT,
                        max_installs BIGINT,
                        score DOUBLE PRECISION,
                        ratings BIGINT,
                        reviews BIGINT,
                        histogram JSONB,
                        price DOUBLE PRECISION,
                        free BOOLEAN,
                        currency TEXT,
                        sale BOOLEAN,
                        sale_time TEXT,
                        original_price DOUBLE PRECISION,
                        developer TEXT,
                        developer_id TEXT,
                        developer_email TEXT,
                        developer_website TEXT,
                        developer_address TEXT,
                        privacy_policy TEXT,
                        genre TEXT,
                        genre_id TEXT,
                        categories JSONB,
                        icon TEXT,
                        header_image TEXT,
                        screenshots JSONB,
                        video TEXT,
                        video_image TEXT,
                        content_rating TEXT,
                        content_rating_description TEXT,
                        ad_supported BOOLEAN,
                        contains_ads BOOLEAN,
                        in_app_purchases BOOLEAN,
                        size TEXT,
                        android_version TEXT,
                        android_version_text TEXT,
                        developer_internal_id TEXT,
                        required_android_version TEXT,
                        interactive_elements TEXT,
                        updated BIGINT,
                        version TEXT,
                        recent_changes TEXT,
                        scraped_at TIMESTAMPTZ DEFAULT NOW()
                    );

                    CREATE TABLE IF NOT EXISTS app_country_stats (
                        id BIGSERIAL PRIMARY KEY,
                        app_id TEXT REFERENCES apps(app_id) ON DELETE CASCADE,
                        country CHAR(2),
                        installs TEXT,
                        min_installs BIGINT,
                        score DOUBLE PRECISION,
                        ratings BIGINT,
                        reviews BIGINT,
                        price DOUBLE PRECISION,
                        free BOOLEAN,
                        scrape_date DATE DEFAULT CURRENT_DATE,
                        scraped_at TIMESTAMPTZ DEFAULT NOW(),
                        UNIQUE (app_id, country, scrape_date)
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON app_queue(status);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_app ON discovery_signals(app_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_stats_country ON app_country_stats(country);")
            conn.commit()
            print("[DB] Tables created / verified.")
        finally:
            self._put_conn(conn)

    def reset_data(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS country_charts CASCADE;")
                cur.execute("""
                    TRUNCATE app_country_stats, apps, discovery_signals, app_queue
                    RESTART IDENTITY CASCADE;
                """)
            conn.commit()
            print("[DB] Existing scraped dataset cleared.")
        finally:
            self._put_conn(conn)

    def add_discovery(self, app_id, source, country=None, category=None, keyword=None, collection=None, chart_rank=None):
        signal_key = "|".join([
            app_id,
            source,
            country or "",
            category or "",
            keyword or "",
            collection or "",
            str(chart_rank or ""),
        ])
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO app_queue (app_id, source_count)
                    VALUES (%s, 1)
                    ON CONFLICT (app_id) DO UPDATE SET
                        source_count = app_queue.source_count + 1,
                        last_discovered_at = NOW();
                """, (app_id,))
                cur.execute("""
                    INSERT INTO discovery_signals
                        (app_id, source, country, category, keyword, collection, chart_rank, signal_key)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (app_id, source, country, category, keyword, collection, chart_rank, signal_key))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            self._put_conn(conn)

    def get_pending_app_ids(self, limit=None):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                sql = """
                    SELECT app_id
                    FROM app_queue
                    WHERE status IN ('pending', 'failed')
                    ORDER BY source_count DESC, first_discovered_at ASC
                """
                if limit:
                    sql += " LIMIT %s"
                    cur.execute(sql, (limit,))
                else:
                    cur.execute(sql)
                return [row[0] for row in cur.fetchall()]
        finally:
            self._put_conn(conn)

    def mark_status(self, app_id, status, min_installs=None, error=None):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE app_queue
                    SET status=%s, min_installs=%s, processed_at=NOW(), last_error=%s
                    WHERE app_id=%s;
                """, (status, min_installs, error, app_id))
            conn.commit()
        finally:
            self._put_conn(conn)

    def upsert_app(self, app_data):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO apps (
                        app_id, title, description, summary, installs, min_installs, max_installs,
                        score, ratings, reviews, histogram, price, free, currency, sale,
                        sale_time, original_price, developer, developer_id, developer_email,
                        developer_website, developer_address, privacy_policy, genre, genre_id,
                        categories, icon, header_image, screenshots, video, video_image,
                        content_rating, content_rating_description, ad_supported, contains_ads,
                        in_app_purchases, size, android_version, android_version_text,
                        developer_internal_id, required_android_version, interactive_elements,
                        updated, version, recent_changes
                    ) VALUES (
                        %(appId)s, %(title)s, %(description)s, %(summary)s, %(installs)s,
                        %(minInstalls)s, %(maxInstalls)s, %(score)s, %(ratings)s, %(reviews)s,
                        %(histogram)s, %(price)s, %(free)s, %(currency)s, %(sale)s,
                        %(saleTime)s, %(originalPrice)s, %(developer)s, %(developerId)s,
                        %(developerEmail)s, %(developerWebsite)s, %(developerAddress)s,
                        %(privacyPolicy)s, %(genre)s, %(genreId)s, %(categories)s, %(icon)s,
                        %(headerImage)s, %(screenshots)s, %(video)s, %(videoImage)s,
                        %(contentRating)s, %(contentRatingDescription)s, %(adSupported)s,
                        %(containsAds)s, %(inAppPurchases)s, %(size)s, %(androidVersion)s,
                        %(androidVersionText)s, %(developerInternalID)s,
                        %(requiredAndroidVersion)s, %(interactiveElements)s, %(updated)s,
                        %(version)s, %(recentChanges)s
                    )
                    ON CONFLICT (app_id) DO UPDATE SET
                        title=EXCLUDED.title,
                        installs=EXCLUDED.installs,
                        min_installs=EXCLUDED.min_installs,
                        max_installs=EXCLUDED.max_installs,
                        score=EXCLUDED.score,
                        ratings=EXCLUDED.ratings,
                        reviews=EXCLUDED.reviews,
                        scraped_at=NOW();
                """, self._prepare_app(app_data))
            conn.commit()
        finally:
            self._put_conn(conn)

    def insert_country_stats(self, rows):
        if not rows:
            return
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute("""
                        INSERT INTO app_country_stats
                            (app_id, country, installs, min_installs, score, ratings, reviews, price, free)
                        VALUES
                            (%(app_id)s, %(country)s, %(installs)s, %(min_installs)s,
                             %(score)s, %(ratings)s, %(reviews)s, %(price)s, %(free)s)
                        ON CONFLICT (app_id, country, scrape_date) DO NOTHING;
                    """, row)
            conn.commit()
        finally:
            self._put_conn(conn)

    def counts(self):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                result = {}
                for table in ("app_queue", "discovery_signals", "apps", "app_country_stats"):
                    cur.execute(f"SELECT COUNT(*) FROM {table};")
                    result[table] = cur.fetchone()[0]
                return result
        finally:
            self._put_conn(conn)

    def _prepare_app(self, app_data):
        result = dict(app_data)
        result.setdefault("maxInstalls", result.get("realInstalls"))
        result.setdefault("inAppPurchases", result.get("offersIAP"))
        for key in ("histogram", "categories", "screenshots"):
            val = result.get(key)
            if val is not None and not isinstance(val, str):
                result[key] = json.dumps(val)
        defaults = {
            "appId": None, "title": None, "description": None, "summary": None,
            "installs": None, "minInstalls": None, "maxInstalls": None,
            "score": None, "ratings": None, "reviews": None, "histogram": None,
            "price": None, "free": None, "currency": None, "sale": False,
            "saleTime": None, "originalPrice": None, "developer": None,
            "developerId": None, "developerEmail": None, "developerWebsite": None,
            "developerAddress": None, "privacyPolicy": None, "genre": None,
            "genreId": None, "categories": None, "icon": None, "headerImage": None,
            "screenshots": None, "video": None, "videoImage": None,
            "contentRating": None, "contentRatingDescription": None,
            "adSupported": None, "containsAds": False, "inAppPurchases": None,
            "size": None, "androidVersion": None, "androidVersionText": None,
            "developerInternalID": None, "requiredAndroidVersion": None,
            "interactiveElements": None, "updated": None, "version": None,
            "recentChanges": None,
        }
        for key, value in defaults.items():
            result.setdefault(key, value)
        return result
