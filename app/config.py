import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TG_API_ID = int(os.getenv("TG_API_ID", "0"))
    TG_API_HASH = os.getenv("TG_API_HASH", "")
    TG_SESSION = os.getenv("TG_SESSION", "ba_events_session")
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
    TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID", "")

    POSTGRES_DB = os.getenv("POSTGRES_DB", "baevents")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "ba")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ba_password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

    TZ = os.getenv("TZ", "America/Argentina/Buenos_Aires")

    ENABLE_STORIES = os.getenv("ENABLE_STORIES", "false").lower() == "true"
    STORY_TOP_N = int(os.getenv("STORY_TOP_N", "3"))
    STORY_MORNING = os.getenv("STORY_MORNING", "11:00")
    STORY_EVENING = os.getenv("STORY_EVENING", "17:00")

    TOPIC_TRANCE = int(os.getenv("TOPIC_TRANCE", "0"))
    TOPIC_DNB = int(os.getenv("TOPIC_DNB", "0"))
    TOPIC_ROCK = int(os.getenv("TOPIC_ROCK", "0"))
    TOPIC_POP = int(os.getenv("TOPIC_POP", "0"))
    TOPIC_INDIE = int(os.getenv("TOPIC_INDIE", "0"))
    TOPIC_METAL = int(os.getenv("TOPIC_METAL", "0"))
    TOPIC_CALENDAR = int(os.getenv("TOPIC_CALENDAR", "0"))
    TOPIC_GENERAL = int(os.getenv("TOPIC_GENERAL", "0"))
    TOPIC_ELECTRONIC = int(os.getenv("TOPIC_ELECTRONIC", "0"))
    TOPIC_HOUSE = int(os.getenv("TOPIC_HOUSE", "0"))
    TOPIC_TECHNO = int(os.getenv("TOPIC_TECHNO", "0"))
    TOPIC_RAP = int(os.getenv("TOPIC_RAP", "0"))
    TOPIC_JAZZ = int(os.getenv("TOPIC_JAZZ", "0"))
    TOPIC_TRANCE = int(os.getenv("TOPIC_TRANCE", "0"))
    TOPIC_DNB = int(os.getenv("TOPIC_DNB", "0"))

    TOPIC_MAP = {
        "general": TOPIC_GENERAL,
        "misc": TOPIC_GENERAL,
        "calendar": TOPIC_CALENDAR,
        "trance": TOPIC_TRANCE,
        "dnb": TOPIC_DNB,
        "rock": TOPIC_ROCK,
        "pop": TOPIC_POP,
        "indie": TOPIC_INDIE,
        "metal": TOPIC_METAL,
        "rap": TOPIC_RAP,
        "jazz": TOPIC_JAZZ,
        "trance": TOPIC_TRANCE,
        "dnb": TOPIC_DNB,
        "electronic": TOPIC_ELECTRONIC or TOPIC_GENERAL,
        "house": TOPIC_HOUSE or TOPIC_ELECTRONIC or TOPIC_GENERAL,
        "techno": TOPIC_TECHNO or TOPIC_ELECTRONIC or TOPIC_GENERAL,
    }

    DEFAULT_LISTEN_BASE = os.getenv("DEFAULT_LISTEN_BASE", "https://music.youtube.com/search?q=")
    DEFAULT_INFO_URL = os.getenv("DEFAULT_INFO_URL", "")
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    _GOOGLE_SEARCH_KEYS_RAW = os.getenv("GOOGLE_SEARCH_API_KEYS", "")
    GOOGLE_SEARCH_API_KEYS = [
        key.strip()
        for key in _GOOGLE_SEARCH_KEYS_RAW.split(",")
        if key.strip()
    ]
    GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX", "")
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
    ENABLE_GENRE_ALERTS = os.getenv("ENABLE_GENRE_ALERTS", "false").lower() == "true"
    LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "")
    OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "")
    VENTI_API_COOKIE = os.getenv("VENTI_API_COOKIE", "")
    VENTI_API_AUTH = os.getenv("VENTI_API_AUTH", "")

    INSTAGRAM_PROFILES = os.getenv("INSTAGRAM_PROFILES", "")
    INSTAGRAM_USER = os.getenv("INSTAGRAM_USER", "")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
