from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from ..utils import normalize_title

CACHE_PATH = Path("storage/cache/artist_genres.json")


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)


def _normalize_key(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    normalized = normalize_title(name)
    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
    normalized = normalized.strip()
    return normalized or None


def get_cached_genres(name: Optional[str]) -> Optional[List[str]]:
    key = _normalize_key(name)
    if not key:
        return None
    cache = _load_cache()
    entry = cache.get(key)
    if entry:
        genres = entry.get("genres") or []
        return list(genres) if genres else None
    return None


def cache_artist_genres(name: Optional[str], genres: Iterable[str]) -> None:
    if not name:
        return
    genres = [g for g in genres if g and g.lower() != "general"]
    if not genres:
        return
    key = _normalize_key(name)
    if not key:
        return
    cache = _load_cache()
    cache[key] = {
        "genres": list(dict.fromkeys(genres)),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _save_cache(cache)
