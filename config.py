import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5433)),
    "dbname": os.getenv("DB_NAME", "playstore"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", ""),
}

WEBSHARE_PROXY_URLS = [
    proxy.strip()
    for proxy in os.getenv("WEBSHARE_PROXIES", os.getenv("WEBSHARE_PROXY", "")).split(",")
    if proxy.strip()
]

# Focus countries: large Android markets plus strong monetization markets.
MARKET_COUNTRIES = ["us", "in", "br", "id", "mx", "gb", "de", "jp", "kr", "ph"]

CATEGORIES = [
    "SOCIAL", "FINANCE", "TOOLS", "GAME", "ENTERTAINMENT",
    "SHOPPING", "EDUCATION", "HEALTH_AND_FITNESS", "TRAVEL_AND_LOCAL",
    "FOOD_AND_DRINK", "PRODUCTIVITY", "COMMUNICATION",
    "MAPS_AND_NAVIGATION", "MUSIC_AND_AUDIO", "PHOTOGRAPHY",
]

CHART_COLLECTIONS = ["topselling_free", "topselling_paid", "topgrossing"]
CHART_COUNT = int(os.getenv("CHART_COUNT", 200))

SEARCH_HITS = int(os.getenv("SEARCH_HITS", 50))
THREADS = int(os.getenv("THREADS", 5))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 45))
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", 4))
MIN_INSTALLS = int(os.getenv("MIN_INSTALLS", 100_000))

# Discovery order is intentional: charts/categories first for famous apps in each
# country, then keyword searches for broader coverage.
BASE_SEARCH_KEYWORDS = [
    # Core AI / utility
    "ai app", "ai tool", "ai assistant", "on-device ai", "offline ai",
    "private ai", "local llm", "gemma", "phi-3", "llm inference",
    "ai productivity", "smart utility", "chatbot",

    # Education / English / study
    "english speaking", "spoken english", "hinglish english", "grammar checker",
    "grammar coach", "pronunciation coach", "interview practice",
    "fresher interview", "resume builder", "cv maker", "study app",
    "exam prep", "gk quiz", "upsc quiz", "ssc quiz", "flashcards",
    "notes to summary", "micro learning",

    # Finance / credit / expense / tax
    "expense tracker", "budget planner", "money manager", "spending tracker",
    "bill reminder", "subscription tracker", "bill splitter", "split expense",
    "emi calculator", "debt payoff", "credit score", "credit booster",
    "cibil score", "finance advisor", "receipt scanner", "invoice scanner",
    "tax tracker", "gig worker tax", "freelancer tax", "mileage tracker",

    # Document / OCR / scanner / notes
    "pdf reader", "pdf summarizer", "ai pdf", "document scanner",
    "smart scanner", "ocr scanner", "notes summarizer", "voice notes to tasks",
    "action item extractor", "meeting notes ai", "doc organizer",

    # Health / fitness / food
    "calorie tracker indian food", "indian diet tracker", "symptom checker",
    "medicine reminder", "workout planner", "chair yoga", "health tips hindi",

    # Beauty / personal utility
    "hairstyle try on", "hair color analyzer", "skin care scanner",
    "ingredient scanner", "personal color analysis", "beauty advisor ai",

    # Devotional / astrology / lifestyle
    "devotional app", "puja guide", "mantra app", "aarti app",
    "festival calendar", "hindu calendar", "astrology app", "horoscope app",
    "kundli", "rashifal",

    # Entertainment / short video / drama
    "short drama", "micro drama", "reels drama", "drama tracker",
    "ai story app", "interactive story", "watch party",
    "vernacular short video", "audio drama",

    # Games / casual / cultural
    "teen patti", "ludo", "ludo king", "gully cricket", "bollywood quiz",
    "cultural games", "casual indian games", "quiz game india",

    # Regional-language discovery
    "hindi app", "tamil app", "telugu app", "bengali app", "marathi app",
    "urdu app", "vernacular app", "regional language app", "india local app",

    # Market / geo expansion
    "india", "tier 2 city", "tier 3 city", "bangladesh", "pakistan",
    "indonesia", "philippines", "vietnam", "indian diaspora",
    "us indian", "uk indian",

    # Competitor / adjacent pull
    "chatgpt", "gemini", "splitwise", "rocket money", "monarch money",
    "mileiq", "astrosage", "astrotalk", "reelshort", "phonepe", "gpay",
    "meesho", "zepto", "whatsapp",
]

KEYWORD_MODIFIERS = [
    "india", "hindi", "offline", "ai", "free",
]


def build_search_keywords():
    keywords = list(dict.fromkeys(BASE_SEARCH_KEYWORDS))
    combination_cores = [
        "expense tracker", "spoken english", "short drama app", "resume builder",
        "pdf scanner", "medicine reminder", "astrology app", "budget planner",
        "photo editor", "video editor", "study app", "invoice scanner",
    ]
    for core in combination_cores:
        for modifier in KEYWORD_MODIFIERS:
            keywords.append(f"{core} {modifier}")
    return list(dict.fromkeys(keywords))


SEARCH_KEYWORDS = build_search_keywords()
