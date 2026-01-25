from __future__ import annotations

from functools import lru_cache
from typing import List, Optional
import json
import logging
from datetime import date
from pathlib import Path

import requests

from ..config import Config

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
TELEGRAM_API_URL = "https://api.telegram.org"
USAGE_PATH = Path("storage/quota/google_usage.json")
QUOTA_WARNING_THRESHOLD = 75

logger = logging.getLogger(__name__)


def _get_key_pool() -> list[str]:
    keys = list(Config.GOOGLE_SEARCH_API_KEYS or [])
    if not keys and Config.GOOGLE_SEARCH_API_KEY:
        keys = [Config.GOOGLE_SEARCH_API_KEY]
    return keys


def _load_usage() -> dict:
    default = {"date": date.today().isoformat(), "keys": {}, "current_index": 0}
    if not USAGE_PATH.exists():
        return default
    try:
        with USAGE_PATH.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except Exception:
        return default

    today = date.today().isoformat()
    if data.get("date") != today:
        return {"date": today, "keys": {}, "current_index": 0}

    if "keys" not in data:
        # migrate old format {"count":..., "alert_sent":...}
        count = data.get("count", 0)
        alert = data.get("alert_sent", False)
        data = {"date": today, "keys": {}, "current_index": 0}
        if count:
            key_pool = _get_key_pool()
            if key_pool:
                data["keys"][key_pool[0]] = {
                    "count": count,
                    "alert_sent": alert,
                    "exhausted": False,
                }
    data.setdefault("keys", {})
    data.setdefault("current_index", 0)
    return data


def _save_usage(data: dict) -> None:
    USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with USAGE_PATH.open("w", encoding="utf-8") as fp:
            json.dump(data, fp)
    except Exception as exc:
        logger.warning("Failed to persist Google usage stats: %s", exc)


def _ensure_key_entry(data: dict, key: str) -> dict:
    keys = data.setdefault("keys", {})
    if key not in keys:
        keys[key] = {"count": 0, "alert_sent": False, "exhausted": False}
    return keys[key]


def _send_admin_alert(message: str) -> None:
    token = Config.TG_BOT_TOKEN
    chat_id = Config.ADMIN_CHAT_ID
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"{TELEGRAM_API_URL}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("Failed to send Google quota alert: %s", exc)


def _register_usage(api_key: str) -> None:
    data = _load_usage()
    info = _ensure_key_entry(data, api_key)
    info["count"] = int(info.get("count", 0)) + 1
    if info["count"] >= QUOTA_WARNING_THRESHOLD and not info.get("alert_sent"):
        info["alert_sent"] = True
        _send_admin_alert(
            f"⚠️ Google Custom Search ({api_key[:6]}…): израсходовано {info['count']} из 100 запросов за сегодня."
        )
        logger.warning(
            "Google Custom Search usage reached %s requests today for key %s.",
            info["count"],
            api_key[:8],
        )
    _save_usage(data)


def _mark_key_exhausted(api_key: str, *, alert: bool = True) -> None:
    data = _load_usage()
    info = _ensure_key_entry(data, api_key)
    info["exhausted"] = True
    _save_usage(data)
    if alert:
        _send_admin_alert(
            f"⛔ Ключ Google Custom Search ({api_key[:6]}…) исчерпал дневную квоту. Переключаюсь на следующий."
        )
    if not _select_key(auto_save=False):
        _send_admin_alert(
            "⛔ Все ключи Google Custom Search исчерпаны. Поиск жанров временно отключён."
        )
        logger.error("All Google Custom Search keys exhausted for today.")


def _select_key(*, auto_save: bool = True) -> Optional[str]:
    pool = _get_key_pool()
    if not pool:
        return None
    data = _load_usage()
    current_index = data.get("current_index", 0) % len(pool)
    for offset in range(len(pool)):
        idx = (current_index + offset) % len(pool)
        key = pool[idx]
        info = _ensure_key_entry(data, key)
        if not info.get("exhausted"):
            data["current_index"] = idx
            if auto_save:
                _save_usage(data)
            return key
    return None


def _handle_limit_exceeded(api_key: str) -> None:
    _mark_key_exhausted(api_key)


def _execute_search(query: str, *, num: int, api_key: str) -> Optional[List[str]]:
    cx = Config.GOOGLE_SEARCH_CX
    if not cx:
        return None
    params = {
        "q": query,
        "num": num,
        "key": api_key,
        "cx": cx,
        "safe": "off",
    }
    response = None
    try:
        _register_usage(api_key)
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception:
        status = getattr(response, "status_code", None)
        if status == 403:
            _handle_limit_exceeded(api_key)
        return None

    snippets: List[str] = []
    for item in data.get("items") or []:
        pieces = []
        title = item.get("title")
        snippet = item.get("snippet")
        if title:
            pieces.append(title)
        if snippet:
            pieces.append(snippet)
        if pieces:
            snippets.append(" ".join(pieces))
    return snippets


@lru_cache(maxsize=128)
def _perform_search(query: str, *, num: int = 5) -> List[str]:
    pool = _get_key_pool()
    if not pool or not Config.GOOGLE_SEARCH_CX:
        return []

    attempts = len(pool)
    for _ in range(attempts):
        api_key = _select_key()
        if not api_key:
            break
        snippets = _execute_search(query, num=num, api_key=api_key)
        if snippets is not None:
            return snippets
    return []


def search_music_genre_snippets(artist: str) -> List[str]:
    """Return snippets from Google Custom Search related to the artist's music genre."""
    if not artist:
        return []
    queries = [
        f"{artist} music genre",
        f"{artist} género musical",
        f"{artist} estilo musical",
    ]
    for query in queries:
        snippets = _perform_search(query)
        if snippets:
            return snippets
    return []
