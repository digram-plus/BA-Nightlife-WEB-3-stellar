from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, List, Sequence

from .config import Config
from .services.google_search import search_music_genre_snippets
from .services.lastfm import fetch_top_tags
from .services.artist_cache import get_cached_genres, cache_artist_genres

GENRE_ORDER: Sequence[str] = (
    "electronic",
    "trance",
    "house",
    "techno",
    "dnb",
    "rock",
    "pop",
    "indie",
    "metal",
    "general",
)

ELECTRONIC_SUBGENRES = {"trance", "house", "techno", "dnb"}

GENRE_KEYWORDS: dict[str, list[str]] = {
    "electronic": [
        "electronic music",
        "electronic festival",
        "electro night",
        "club night",
        "club event",
        "dance music",
        "edm",
        "#edm",
        "electronic set",
    ],
    "trance": [
        "trance",
        "#trance",
        "uplifting",
        "progressive trance",
        "psytrance",
        "melodic trance",
        "asot",
    ],
    "house": [
        "house",
        "#house",
        "house music",
        "deep house",
        "deep-house",
        "tech house",
        "tech-house",
        "afro house",
        "afro-house",
        "minimal house",
    ],
    "techno": [
        "techno",
        "#techno",
        "melodic techno",
        "minimal techno",
        "acid techno",
    ],
    "dnb": [
        "dnb",
        "#dnb",
        "drum and bass",
        "drum & bass",
        "drum n bass",
        "neurofunk",
        "liquid dnb",
        "jungle",
    ],
    "rock": [
        "rock",
        "#rock",
        "punk",
        "grunge",
        "hard rock",
        "alternate rock",
        "stoner rock",
    ],
    "pop": [
        "pop",
        "#pop",
        "mainstream pop",
        "dance pop",
        "latino pop",
        "chart pop",
    ],
    "indie": [
        "indie",
        "#indie",
        "indie pop",
        "indie rock",
        "alt",
        "alternative",
        "dream pop",
    ],
    "metal": [
        "metal",
        "#metal",
        "heavy metal",
        "death metal",
        "thrash",
        "black metal",
    ],
}

KEYWORD_PATTERNS: dict[str, re.Pattern[str]] = {
    keyword: re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE)
    for keywords in GENRE_KEYWORDS.values()
    for keyword in keywords
}


# Хардкод для повторяющихся артистов/серий мероприятий
ARTIST_GENRE: dict[str, Sequence[str]] = {
    "armin van buuren": ("trance",),
    "adam beyer": ("techno",),
    "korolova": ("house",),
    "victoria engel": ("house",),
    "nicolas taboada": ("techno",),
    "ultra": ("electronic",),
    "resistance": ("techno",),
    "franky rizado": ("house",),
    "franky rizardo": ("house",),
}

LASTFM_TAG_MAP: dict[str, Iterable[str]] = {
    "electronic": ["electronic", "edm", "electronica", "club", "club music"],
    "trance": ["trance", "uplifting trance", "progressive trance", "psytrance"],
    "house": ["house", "deep house", "tech house", "afro house", "minimal house"],
    "techno": ["techno", "melodic techno", "minimal techno", "acid techno"],
    "dnb": ["drum and bass", "drum & bass", "dnb", "jungle", "neurofunk"],
    "rock": ["rock", "classic rock", "hard rock", "punk"],
    "pop": ["pop", "dance pop", "latin pop"],
    "indie": ["indie", "indie pop", "indie rock", "alternative"],
    "metal": ["metal", "heavy metal", "death metal", "thrash metal"],
}


def _match_keywords(text: str) -> set[str]:
    hits: set[str] = set()
    lowered = text.lower()
    for genre, keywords in GENRE_KEYWORDS.items():
        for keyword in keywords:
            pattern = KEYWORD_PATTERNS[keyword]
            if pattern.search(lowered):
                hits.add(genre)
                break
    return hits


def _normalize(genres: Iterable[str]) -> list[str]:
    unique = []
    seen = set()
    for genre in genres:
        if not genre or genre in seen:
            continue
        seen.add(genre)
        unique.append(genre)
    ordered = [g for g in GENRE_ORDER if g in seen]
    for g in unique:
        if g not in ordered:
            ordered.append(g)
    return ordered or ["general"]


def _map_lastfm_tags(tags: Iterable[str]) -> set[str]:
    mapped: set[str] = set()
    for tag in tags:
        tag_lower = tag.lower()
        for genre, synonyms in LASTFM_TAG_MAP.items():
            if tag_lower in synonyms:
                mapped.add(genre)
    return mapped


UPPERCASE_PATTERN = re.compile(r"\b([A-Z][A-Z0-9 .'\-]{2,})\b")


def _candidate_names(hints: Iterable[str]) -> List[str]:
    candidates: List[str] = []
    seen: set[str] = set()
    splitter = re.compile(r"[-–/,|•()\n\r]|\b(?:b2b|feat\.?|ft\.?|vs\.?|x)\b", re.IGNORECASE)
    for hint in hints:
        if not hint:
            continue
        for part in splitter.split(hint):
            name = part.strip()
            if name and len(name) > 1:
                lowered = name.lower()
                if lowered not in seen:
                    seen.add(lowered)
                    candidates.append(name)
        for match in UPPERCASE_PATTERN.findall(hint):
            name = match.strip()
            if name and len(name) > 1:
                lowered = name.lower()
                if lowered not in seen:
                    seen.add(lowered)
                    candidates.append(name)
    return candidates


@lru_cache(maxsize=128)
def _google_genre_lookup(name: str) -> set[str]:
    snippets = search_music_genre_snippets(name)
    hits: set[str] = set()
    for snippet in snippets:
        hits.update(_match_keywords(snippet))
    return hits


def _ensure_electronic(genres: set[str], combined_text: str) -> None:
    if genres.intersection(ELECTRONIC_SUBGENRES):
        genres.add("electronic")
        return
    if "electronic" in genres:
        return
    if _match_keywords(combined_text).intersection({"electronic"}):
        genres.add("electronic")


def detect_genres(text: str, hints: list[str] | None = None) -> list[str]:
    sources = [text] + (hints or [])
    combined_text = " ".join(filter(None, sources))
    combined_lower = combined_text.lower()

    genres: set[str] = set()
    candidate_names = _candidate_names(sources)

    for name in candidate_names:
        cached = get_cached_genres(name)
        if cached:
            return _normalize(cached)

    # 1. прямое совпадение артистов/брендов
    for artist, preset in ARTIST_GENRE.items():
        if artist in combined_lower:
            genres.update(preset)

    # 2. ключевые слова в тексте
    for chunk in sources:
        if not chunk:
            continue
        genres.update(_match_keywords(chunk))

    # 3. Last.fm
    if Config.LASTFM_API_KEY:
        for name in candidate_names:
            tags = fetch_top_tags(name)
            mapped = _map_lastfm_tags(tags)
            if mapped:
                cache_artist_genres(name, mapped)
                genres.update(mapped)
                break

    # 4. Google fallback, если всё ещё пусто
    key_pool = list(Config.GOOGLE_SEARCH_API_KEYS or [])
    if Config.GOOGLE_SEARCH_API_KEY and Config.GOOGLE_SEARCH_API_KEY not in key_pool:
        key_pool.append(Config.GOOGLE_SEARCH_API_KEY)
    if not genres and key_pool and Config.GOOGLE_SEARCH_CX:
        for name in candidate_names:
            hits = _google_genre_lookup(name)
            if hits:
                cache_artist_genres(name, hits)
                genres.update(hits)
                break

    if genres:
        _ensure_electronic(genres, combined_lower)
        return _normalize(genres)

    return ["general"]
