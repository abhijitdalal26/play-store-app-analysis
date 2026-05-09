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
# country, then global + country-specific keyword searches for broader coverage.
GLOBAL_SEARCH_KEYWORDS = [
    # Core AI / utility
    "ai app", "ai tool", "ai assistant", "on-device ai", "offline ai",
    "private ai", "local llm", "gemma", "phi-3", "llm inference",
    "ai productivity", "smart utility", "chatbot",

    # Education / English / study
    "english speaking", "spoken english", "grammar checker",
    "grammar coach", "pronunciation coach", "interview practice",
    "fresher interview", "resume builder", "cv maker", "study app",
    "exam prep", "flashcards",
    "notes to summary", "micro learning",

    # Finance / credit / expense / tax
    "expense tracker", "budget planner", "money manager", "spending tracker",
    "bill reminder", "subscription tracker", "bill splitter", "split expense",
    "emi calculator", "debt payoff", "credit score", "credit booster",
    "finance advisor", "receipt scanner", "invoice scanner",
    "tax tracker", "gig worker tax", "freelancer tax", "mileage tracker",

    # Document / OCR / scanner / notes
    "pdf reader", "pdf summarizer", "ai pdf", "document scanner",
    "smart scanner", "ocr scanner", "notes summarizer", "voice notes to tasks",
    "action item extractor", "meeting notes ai", "doc organizer",

    # Health / fitness / food
    "calorie tracker", "diet tracker", "symptom checker",
    "medicine reminder", "workout planner", "chair yoga", "health tips",

    # Beauty / personal utility
    "hairstyle try on", "hair color analyzer", "skin care scanner",
    "ingredient scanner", "personal color analysis", "beauty advisor ai",

    # Devotional / astrology / lifestyle
    "devotional app", "festival calendar", "astrology app", "horoscope app",

    # Entertainment / short video / drama
    "short drama", "micro drama", "reels drama", "drama tracker",
    "ai story app", "interactive story", "watch party",
    "short video", "audio drama",

    # Games / casual / cultural
    "ludo", "quiz game", "cultural games", "casual games", "puzzle game",
    "racing game", "car game", "battle royale", "shooting game",
    "strategy game", "card game", "word game", "offline game", "kids game",
    "sports game", "football game", "cricket game", "anime game", "rpg game",
    "simulation game", "arcade game", "mahjong", "sudoku", "solitaire",
    "chess", "idle game", "merge game", "coloring game", "brain game",
    "trivia game",

    # Simple solo-buildable utilities and app ideas
    "qr scanner", "barcode scanner", "unit converter", "currency converter",
    "age calculator", "bmi calculator", "loan calculator", "tip calculator",
    "password manager", "habit tracker", "water reminder", "pomodoro timer",
    "countdown timer", "stopwatch", "voice recorder", "screen recorder",
    "call recorder", "file manager", "duplicate photo remover",
    "photo compressor", "image resizer", "background remover", "meme maker",
    "sticker maker", "caption generator", "hashtag generator",
    "quote maker", "poster maker", "logo maker", "business card maker",
    "invoice maker", "resume maker", "cover letter maker", "job tracker",
    "daily planner", "meal planner", "grocery list", "recipe app",
    "period tracker", "baby tracker", "pet care", "plant care",
    "expense manager", "inventory tracker", "warranty tracker",
    "subscription reminder", "medicine tracker", "prayer times",

    # Competitor / adjacent pull
    "chatgpt", "gemini", "splitwise", "rocket money", "monarch money",
    "mileiq", "astrosage", "astrotalk", "reelshort", "phonepe", "gpay",
    "meesho", "zepto", "whatsapp",
]

COUNTRY_SEARCH_KEYWORDS = {
    "us": [
        "credit builder", "side hustle", "tax refund", "tax filing",
        "meal planner", "mental health", "therapy app", "habit tracker",
        "subscription manager", "cash advance", "coupon app", "job search",
        "dating app", "sports betting", "college app", "student loan",
    ],
    "gb": [
        "credit score uk", "council tax", "hmrc", "train tickets",
        "nhs app", "gp appointment", "budget planner uk", "cashback uk",
        "football scores", "job search uk", "driving theory test",
        "parking app",
    ],
    "in": [
        "hinglish english", "gk quiz", "upsc quiz", "ssc quiz",
        "cibil score", "calorie tracker indian food", "indian diet tracker",
        "health tips hindi", "puja guide", "mantra app", "aarti app",
        "hindu calendar", "kundli", "rashifal", "teen patti",
        "gully cricket", "bollywood quiz", "casual indian games",
        "hindi app", "tamil app", "telugu app", "bengali app",
        "marathi app", "urdu app", "vernacular app", "india local app",
        "tier 2 city", "tier 3 city", "phonepe", "gpay", "meesho",
        "zepto", "expense tracker hindi india", "spoken english offline",
        "short drama app india",
    ],
    "br": [
        "pix", "boleto", "cpf", "credito", "emprestimo", "financas pessoais",
        "controle financeiro", "nota fiscal", "cupom", "futebol", "novela",
        "receitas", "entrega comida", "mercado", "onibus", "biblia",
        "musica brasileira", "namoro", "trabalho",
    ],
    "mx": [
        "credito", "prestamo", "finanzas personales", "factura",
        "sat mexico", "cupones", "futbol", "novelas", "recetas",
        "envios dinero", "banco mexico", "trabajo", "biblia",
        "clima mexico", "transporte", "comida a domicilio",
    ],
    "id": [
        "pinjol", "dompet digital", "pulsa", "ojek online",
        "belajar bahasa inggris", "drama pendek", "islami", "jadwal sholat",
        "alquran", "kalkulator zakat", "belanja online",
        "game penghasil uang", "cek ongkir", "lowongan kerja",
        "kredit online", "resep masakan",
    ],
    "jp": [
        "manga", "anime", "point app", "qr payment", "train route",
        "english study", "kanji", "idol", "gacha", "weather japan",
        "part time job", "recipe japan", "beauty camera", "web novel",
        "cashless payment", "japanese dictionary",
    ],
    "kr": [
        "webtoon", "kpop", "delivery korea", "subway korea", "english study",
        "beauty camera", "point app", "banking korea", "dating korea", "idol",
        "korean dictionary", "job korea", "food delivery", "study planner",
        "skin care",
    ],
    "ph": [
        "gcash", "load", "peso loan", "remittance", "english learning",
        "job finder", "bible", "karaoke", "basketball", "pay bills",
        "online lending", "ofw", "pinoy movies", "tagalog app",
        "food delivery philippines", "budget planner philippines",
    ],
    "de": [
        "steuer", "steuererklärung", "krankenkasse", "deutsch lernen",
        "job suche", "bahn", "fahrplan", "budget planner", "cashback",
        "fußball", "kleinanzeigen", "rechnung scanner", "parking app",
        "meal planner", "mental health", "banking germany",
    ],
}

KEYWORD_MODIFIERS_BY_COUNTRY = {
    "us": ["free", "ai", "offline"],
    "gb": ["uk", "free", "ai"],
    "in": ["india", "hindi", "offline", "ai", "free"],
    "br": ["brasil", "portugues", "gratis"],
    "mx": ["mexico", "espanol", "gratis"],
    "id": ["indonesia", "bahasa indonesia", "gratis"],
    "jp": ["japan", "japanese", "free"],
    "kr": ["korea", "korean", "free"],
    "ph": ["philippines", "tagalog", "free"],
    "de": ["deutschland", "deutsch", "kostenlos"],
}


def build_search_keywords(country=None):
    keywords = list(GLOBAL_SEARCH_KEYWORDS)
    if country:
        keywords.extend(COUNTRY_SEARCH_KEYWORDS.get(country, []))
    combination_cores = [
        "expense tracker", "spoken english", "short drama app", "resume builder",
        "pdf scanner", "medicine reminder", "astrology app", "budget planner",
        "photo editor", "video editor", "study app", "invoice scanner",
        "habit tracker", "qr scanner", "loan calculator", "poster maker",
        "sticker maker", "background remover", "daily planner",
        "period tracker", "water reminder", "voice recorder",
    ]
    modifiers = KEYWORD_MODIFIERS_BY_COUNTRY.get(country, ["free"]) if country else ["free"]
    for core in combination_cores:
        for modifier in modifiers:
            keywords.append(f"{core} {modifier}")
    return list(dict.fromkeys(keywords))


SEARCH_KEYWORDS = sorted(set(
    keyword
    for country in MARKET_COUNTRIES
    for keyword in build_search_keywords(country)
))
