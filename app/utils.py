import hashlib
import os
import re
from datetime import date as ddate

import dateparser
import pytz

TZ = pytz.timezone(os.getenv("TZ", "America/Argentina/Buenos_Aires"))

TIME_REGEX = re.compile(
    r"\b([01]?\d|2[0-3])[:.][0-5]\d\b|\b([01]?\d|2[0-3])\s?(hs|hrs|h)\b",
    re.IGNORECASE,
)


def normalize_title(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def make_hash(title_norm: str, date_iso: str, venue: str | None) -> str:
    base = f"{title_norm}|{date_iso}|{(venue or '').lower()}"
    return hashlib.sha256(base.encode()).hexdigest()


def parse_date(text: str):
    if not text:
        return None, None
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
