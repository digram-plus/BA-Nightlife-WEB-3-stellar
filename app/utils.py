import hashlib
import os
import re
from datetime import date as ddate, time as dtime, datetime
from typing import Optional

import dateparser
import pytz

TZ = pytz.timezone(os.getenv("TZ", "America/Argentina/Buenos_Aires"))

TIME_REGEX = re.compile(
    r"\b([01]?\d|2[0-3])[:.][0-5]\d\b|\b([01]?\d|2[0-3])\s?(hs|hrs|h)\b",
    re.IGNORECASE,
)

DATE_REGEX = re.compile(
    r"\b([0-3]?\d)[/.-]([01]?\d|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:[/.-]([0-9]{2,4}))?\b",
    re.IGNORECASE,
)

TIME_EXTRACT_REGEX = re.compile(
    r"\b([01]?\d|2[0-3])[:.](\d{2})\b|\b([01]?\d|2[0-3])\s?(?:hs|hrs|h)\b",
    re.IGNORECASE,
)


def normalize_title(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def make_hash(title_norm: str, date_iso: str, venue: Optional[str]) -> str:
    base = f"{title_norm}|{date_iso}|{(venue or '').lower()}"
    return hashlib.sha256(base.encode()).hexdigest()


def parse_date(text: str):
    if not text:
        return None, None
    explicit = _parse_explicit_date(text)
    if explicit[0]:
        return explicit
    try:
        dt = dateparser.parse(
            text,
            settings={
                "TIMEZONE": str(TZ),
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
            },
        )
    except (RecursionError, Exception):
        return None, None
    if not dt:
        return None, None

    time_obj = dt.timetz().replace(tzinfo=None)
    search_source = text if isinstance(text, str) else str(text or "")
    if not TIME_REGEX.search(search_source):
        time_obj = None

    return dt.date(), time_obj


def _parse_explicit_date(text: str):
    match = DATE_REGEX.search(text)
    if not match:
        return None, None

    day = int(match.group(1))
    month_raw = match.group(2).lower()
    
    months_map = {
        "ene": 1, "jan": 1,
        "feb": 2,
        "mar": 3,
        "abr": 4, "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8, "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dic": 12, "dec": 12
    }
    
    if month_raw.isdigit():
        month = int(month_raw)
    else:
        month = months_map.get(month_raw[:3], 1)

    year_raw = match.group(3)

    today = datetime.now(TZ).date()
    if year_raw:
        year = int(year_raw)
        if year < 100:
            year += 2000
    else:
        year = today.year

    try:
        candidate = ddate(year, month, day)
    except ValueError:
        return None, None

    if not year_raw and candidate < today:
        if today.month - month >= 6:
            candidate = ddate(year + 1, month, day)
        else:
            return None, None

    time_obj = None
    time_match = TIME_EXTRACT_REGEX.search(text)
    if time_match:
        if time_match.group(1) and time_match.group(2):
            time_obj = dtime(int(time_match.group(1)), int(time_match.group(2)))
        elif time_match.group(3):
            time_obj = dtime(int(time_match.group(3)), 0)

    return candidate, time_obj


def detect_city(text: str) -> str:
    """
    Detects the city name from text.
    Defaults to "Buenos Aires".
    """
    text_lower = (text or "").lower()
    
    cities = {
        "La Plata": ["la plata", "lp", "ensenada", "berisso"],
        "Cordoba": ["cordoba", "córdoba", "cba"],
        "Mendoza": ["mendoza", "mza", "luján de cuyo", "maipú"],
        "Rosario": ["rosario", "santa fe"],
        "Mar del Plata": ["mar del plata", "mdp", "chapadmalal"],
    }
    
    for city_name, keywords in cities.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return city_name
                
    return "Buenos Aires"
