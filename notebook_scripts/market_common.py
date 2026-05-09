from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_PATHS = [
    ROOT / "data" / "google-play-dataset-by-tapivedotcom.csv",
    ROOT / "google-play-dataset" / "google-play-dataset-by-tapivedotcom.csv",
]
CSV_PATH = next((path for path in DATA_PATHS if path.exists()), DATA_PATHS[0])
OUTPUT_DIR = ROOT / "analysis_outputs"

GAME_GENRES = (
    "'Action','Adventure','Arcade','Board','Card','Casino','Casual','Educational',"
    "'Music','Puzzle','Racing','Role Playing','Simulation','Sports','Strategy','Trivia','Word'"
)

ARCHETYPE_SQL = """
CASE
    WHEN regexp_matches(searchable_text, '(wallpaper|theme|launcher|icon pack|background)') THEN 'Personalization: wallpapers/themes/launchers'
    WHEN regexp_matches(searchable_text, '(photo editor|camera|selfie|beauty camera|filter|collage|photo frame|image editor|video editor|video maker|slideshow|movie maker|screen recorder)') THEN 'Photo/video creation tools'
    WHEN regexp_matches(searchable_text, '(music player|mp3|radio|podcast|audio player|ringtone)') THEN 'Music/audio players and radio'
    WHEN regexp_matches(searchable_text, '(scanner|pdf|ocr|document|qr|barcode)') THEN 'Scanner/PDF/QR utilities'
    WHEN regexp_matches(searchable_text, '(calculator|converter|unit converter|bmi|loan|emi|age calculator|tip calculator|tax calculator)') THEN 'Calculators and converters'
    WHEN regexp_matches(searchable_text, '(keyboard|emoji|font|typing)') THEN 'Keyboard/font/emoji utilities'
    WHEN regexp_matches(searchable_text, '(cleaner|booster|battery saver|file manager|antivirus|vpn|browser|download manager)') THEN 'Phone maintenance/security/browser tools'
    WHEN regexp_matches(searchable_text, '(weather|forecast|radar)') THEN 'Weather apps'
    WHEN regexp_matches(searchable_text, '(expense|budget|money manager|finance|loan|credit|bank|wallet|payment|invest|stock|crypto)') THEN 'Finance and money tools'
    WHEN regexp_matches(searchable_text, '(fitness|workout|calorie|diet|weight loss|health|meditation|yoga|sleep|period tracker)') THEN 'Health, fitness, wellness'
    WHEN regexp_matches(searchable_text, '(recipe|food delivery|restaurant|grocery|meal|cooking)') THEN 'Food, recipe, grocery, delivery'
    WHEN regexp_matches(searchable_text, '(shopping|coupon|deals|cashback|store|marketplace)') THEN 'Shopping/deals/marketplace'
    WHEN regexp_matches(searchable_text, '(map|navigation|gps|traffic|transit|bus|train|taxi|parking|travel|hotel|flight)') THEN 'Travel, maps, transport'
    WHEN regexp_matches(searchable_text, '(dating|chat|meet|social|messenger|community|friends)') THEN 'Social, chat, dating'
    WHEN regexp_matches(searchable_text, '(english|language|learn|dictionary|translator|grammar|pronunciation)') THEN 'Language learning/translation'
    WHEN regexp_matches(searchable_text, '(quiz|exam|test prep|flashcard|study|school|math|science|kids learning|education)') THEN 'Education, quiz, exam prep'
    WHEN regexp_matches(searchable_text, '(bible|quran|prayer|devotional|mantra|astrology|horoscope|calendar|festival)') THEN 'Religion/astrology/calendar'
    WHEN regexp_matches(searchable_text, '(news|magazine|newspaper|breaking news)') THEN 'News/media readers'
    WHEN regexp_matches(searchable_text, '(job|resume|cv|career|interview)') THEN 'Jobs/resume/career'
    WHEN genre IN ({game_genres}) THEN 'Games'
    ELSE 'Other / broad app'
END
""".format(game_genres=GAME_GENRES)


def csv_literal(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def require_dataset() -> Path:
    if not CSV_PATH.exists():
        searched = "\n".join(str(path) for path in DATA_PATHS)
        raise FileNotFoundError(f"Historical CSV not found. Looked in:\n{searched}")
    return CSV_PATH


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR
