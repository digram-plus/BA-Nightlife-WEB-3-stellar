from __future__ import annotations

from functools import lru_cache
from typing import List

import requests

from ..config import Config

LASTFM_ENDPOINT = "https://ws.audioscrobbler.com/2.0/"


@lru_cache(maxsize=256)
def fetch_top_tags(artist: str) -> List[str]:
    """Return top tag names for the given artist using Last.fm API."""
    api_key = Config.LASTFM_API_KEY
    if not api_key or not artist:
        return []

    params = {
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": api_key,
        "format": "json",
    }

    try:
        resp = requests.get(LASTFM_ENDPOINT, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    tags = data.get("toptags", {}).get("tag", [])
    names: List[str] = []
    for tag in tags:
        name = tag.get("name")
        if name:
            names.append(name.lower())
    return names

