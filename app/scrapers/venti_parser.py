from __future__ import annotations

import re
import math
from datetime import datetime
import unicodedata
import logging
import json
from urllib.parse import urljoin, urlparse
from typing import Optional

import requests
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import normalize_title, make_hash, parse_date, TZ
from ..config import Config
from .link_utils import (
    extract_canonical_html,
    extract_canonical_via_browser,
)


API_URL = "https://venti.com.ar/api/home/events"
VENTI_BASE = "https://venti.com.ar"
DETAIL_API_URL = "https://venti.com.ar/api/events/{identifier}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://venti.com.ar/eventos",
    "Platform": "web",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
}
if Config.VENTI_API_COOKIE:
    HEADERS["Cookie"] = Config.VENTI_API_COOKIE
if Config.VENTI_API_AUTH:
    HEADERS["Authorization"] = Config.VENTI_API_AUTH
PAGE_SIZE = 50
DETAIL_CACHE: dict[str, dict] = {}
logger = logging.getLogger("venti_parser")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _parse_datetime(value: Optional[str]):
    if not value:
        return None, None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone(TZ).replace(tzinfo=None)
        return dt.date(), dt.time()
    except Exception:
        return parse_date(value)


def _collect_texts(*values: object) -> list[str]:
    texts: list[str] = []
    for value in values:
        if not value:
            continue
        if isinstance(value, (list, tuple, set)):
            texts.extend(str(v) for v in value if v)
        else:
            texts.append(str(value))
    return texts


def _short_text(value, limit=255) -> Optional[str]:
    """Return a string limited to the given length."""
    if not value:
        return None
    if isinstance(value, dict):
        value = (
            value.get("name")
            or value.get("readableAddress")
            or value.get("city")
            or str(value)
        )
    text = str(value).strip()
    if not text:
        return None
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def _best_value(data: dict, *keys, default=None):
    for key in keys:
        if not key:
            continue
        if isinstance(key, str):
            if key in data and data[key]:
                return data[key]
        else:
            current = data
            valid = True
            for part in key:
                if isinstance(part, int):
                    if isinstance(current, (list, tuple)) and 0 <= part < len(current):
                        current = current[part]
                    else:
                        valid = False
                        break
                else:
                    if not isinstance(current, dict) or part not in current:
                        valid = False
                        break
                    current = current[part]
            if valid and current:
                return current
    return default


def _normalize_slug_candidate(value: object) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, dict):
        for key in ("slug", "path", "url", "href", "canonical", "permalink"):
            slug = _normalize_slug_candidate(value.get(key))
            if slug:
                return slug
        return None

    text = str(value).strip()
    if not text:
        return None
    if text.startswith("http"):
        parsed = urlparse(text)
        text = parsed.path or ""
    text = text.replace("\\", "/").split("?", 1)[0].split("#", 1)[0]
    text = text.strip("/")
    if not text:
        return None
    parts = [p for p in text.split("/") if p]
    if not parts:
        return None
    # предпочитаем последний сегмент после "evento"/"event"
    if parts[0] in {"evento", "event", "eventos", "events"} and len(parts) > 1:
        candidate = parts[-1]
    else:
        candidate = parts[-1]
    candidate = candidate.strip()
    if not candidate or candidate.isdigit():
        return None
    return candidate


def _extract_slug(item: dict) -> Optional[str]:
    candidates = (
        item.get("slug"),
        item.get("slugFriendly"),
        item.get("slug_path"),
        item.get("slugPath"),
        item.get("urlName"),
        item.get("url_name"),
        item.get("url"),
        item.get("urlFriendly"),
        item.get("seoSlug"),
        item.get("seo_slug"),
        item.get("seoPath"),
        item.get("seo_path"),
        item.get("seoUrl"),
        item.get("seo_url"),
        item.get("path"),
        item.get("uri"),
        item.get("route"),
        item.get("permalink"),
        item.get("canonicalUrl"),
        item.get("canonical"),
        item.get("seo"),
        item.get("seoData"),
    )
    for candidate in candidates:
        slug = _normalize_slug_candidate(candidate)
        if slug:
            return slug
    return None


SLUG_CLEAN_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: object) -> Optional[str]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    normalized = normalized.lower()
    normalized = SLUG_CLEAN_RE.sub("-", normalized).strip("-")
    return normalized or None


def _normalize_media_url(value: object) -> Optional[str]:
    """Return absolute URL for media if available."""
    if not value:
        return None

    url: Optional[str] = None
    if isinstance(value, str):
        url = value.strip()
    elif isinstance(value, dict):
        for key in ("url", "src", "image", "default", "original"):
            raw = value.get(key)
            if raw:
                url = str(raw).strip()
                break

    if not url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = urljoin(VENTI_BASE, url.lstrip("/"))
    return url


def _build_event_link(item: dict, slug_override: Optional[str] = None) -> str:
    slug = slug_override or _extract_slug(item)
    if slug:
        if slug.startswith("http"):
            return slug
        return urljoin(VENTI_BASE, f"evento/{slug}")

    url = item.get("url") or item.get("permalink")
    if isinstance(url, str) and url.strip():
        link = url.strip()
        if link.startswith("http"):
            return link
        return urljoin(VENTI_BASE, link.lstrip("/"))

    event_id = item.get("id")
    if event_id:
        return urljoin(VENTI_BASE, f"evento/{event_id}")
    return VENTI_BASE


def _pick_best_link(session: requests.Session, item: dict, slug_hint: Optional[str]) -> str:
    candidates: list[str] = []

    # 1) slug из API/деталей
    slug = slug_hint or _extract_slug(item)
    if slug:
        candidates.append(urljoin(VENTI_BASE, f"evento/{slug}"))

    # 2) permalink/url если есть
    url = item.get("url") or item.get("permalink")
    if isinstance(url, str) and url.strip():
        link = url.strip()
        if link.startswith("http"):
            candidates.append(link)
        else:
            candidates.append(urljoin(VENTI_BASE, link.lstrip("/")))

    # 3) fallback: slugify по названию
    slug_fallback = _slugify(
        _best_value(
            item,
            "slugText",
            "name",
            "title",
            ("seo", "title"),
            default=None,
        )
    )
    if slug_fallback:
        candidates.append(urljoin(VENTI_BASE, f"evento/{slug_fallback}"))

    # 4) крайний случай — id
    event_id = item.get("id")
    if event_id:
        candidates.append(urljoin(VENTI_BASE, f"evento/{event_id}"))

    seen = set()
    unique = []
    for link in candidates:
        if link in seen:
            continue
        seen.add(link)
        unique.append(link)

    first_working: Optional[str] = None
    for link in unique:
        try:
            resp = session.get(link, timeout=10, allow_redirects=True)
            if 200 <= resp.status_code < 400:
                canonical = extract_canonical_html(resp.text)
                if canonical:
                    return canonical
                browser_canonical = extract_canonical_via_browser(resp.url or link)
                if browser_canonical:
                    return browser_canonical
                # если редирект на главную событий — пробуем следующий кандидат
                if resp.url and "/eventos" in resp.url:
                    continue
                # иначе запоминаем первый рабочий URL (с учётом редиректа)
                first_working = resp.url or link
        except Exception:
            continue
    if first_working:
        return first_working
    return unique[0] if unique else VENTI_BASE


def _fetch_event_details(session: requests.Session, item: dict) -> Optional[dict]:
    candidates: list[str] = []
    for key in (
        "slug",
        "urlName",
        "urlFriendly",
        "url",
        "path",
        "seoSlug",
        "seo_path",
        "seo",
    ):
        value = item.get(key)
        slug = _normalize_slug_candidate(value)
        if slug and slug not in candidates:
            candidates.append(slug)

    event_id = item.get("id")
    if event_id is not None:
        candidates.append(str(event_id))

    for identifier in candidates:
        if not identifier:
            continue
        identifier_norm = identifier.strip("/ ")
        if not identifier_norm:
            continue
        if identifier_norm in DETAIL_CACHE:
            return DETAIL_CACHE[identifier_norm]
        try:
            resp = session.get(
                DETAIL_API_URL.format(identifier=identifier_norm),
                timeout=20,
            )
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                event_payload = data.get("event") or data
            else:
                event_payload = None
            if not isinstance(event_payload, dict):
                continue
            DETAIL_CACHE[identifier_norm] = event_payload
            return event_payload
        except Exception:
            continue
    return None


def _extract_og_image(url: str, session: requests.Session) -> Optional[str]:
    """Try to pull og:image/twitter:image from the event page."""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return None

    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def run(limit: int = None, force_publish: bool = False):
    print("[venti] Fetching events…")
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        resp = session.get(API_URL, params={"limit": 1, "page": 1}, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        print(f"[venti] Failed to fetch events metadata: {exc}")
        return

    total_items = payload.get("totalItems") or 0
    total_pages = payload.get("totalPages") or 1
    if total_items and total_pages:
        pages = total_pages
    else:
        pages = max(1, math.ceil(total_items / PAGE_SIZE))

    db: Session = SessionLocal()
    created = 0
    updated = 0
    seen_hashes: dict[str, dict[str, object]] = {}
    try:
        for page in range(1, pages + 1):
            if limit and (created + updated) >= limit:
                break
            try:
                resp = session.get(
                    API_URL,
                    params={"limit": PAGE_SIZE, "page": page},
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                print(f"[venti] Failed to fetch page {page}: {exc}")
                continue

            for item in data.get("events", []):
                if limit and (created + updated) >= limit:
                    break
                
                title = item.get("name") or item.get("title")
                if not title:
                    continue

                item_id = item.get("id")
                description = _best_value(
                    item,
                    "description",
                    "summary",
                    ("details",),
                    default="",
                )
                location_text = _best_value(
                    item,
                    "venue",
                    "venueName",
                    "clubName",
                    "locationName",
                    ("location", "name"),
                    default=None,
                )
                location_text_str = _short_text(location_text)
                venue_address = _best_value(
                    item,
                    "address",
                    ("location", "address"),
                    default=None,
                )
                venue_address_str = _short_text(venue_address)
                city = _best_value(
                    item,
                    "city",
                    ("location", "city"),
                    default="Buenos Aires",
                )
                city_str = _short_text(city) or "Buenos Aires"

                start_date = item.get("startDate") or item.get("start_date")
                end_date = item.get("endDate") or item.get("end_date")
                date, time = _parse_datetime(start_date)
                if not date:
                    date, time = parse_date(start_date or description or title)
                if not date:
                    continue

                title_norm = normalize_title(title)
                dedupe = make_hash(title_norm, date.isoformat(), location_text_str)

                slug_hint = _extract_slug(item)

                media_raw = _best_value(
                    item,
                    "cover",
                    "coverImage",
                    "featuredImage",
                    "cardImage",
                    "image",
                    "imageUrl",
                    "imageURL",
                    ("media", "cover"),
                    ("media", "image"),
                    ("media", "picture"),
                    ("pictures", "cover"),
                    ("pictures", "main"),
                    ("pictures", "card"),
                    default=None,
                )
                media_url = _normalize_media_url(media_raw)

                detail_payload = _fetch_event_details(session, item)
                if detail_payload:
                    detail_media = _best_value(
                        detail_payload,
                        "bannerImg",
                        "promoImg",
                        "image",
                        "cover",
                        "coverImage",
                        ("media", "cover"),
                        ("media", "image"),
                        ("images", 0, "url"),
                        ("images", 0, "src"),
                        default=None,
                    )
                    media_url = _normalize_media_url(detail_media) or media_url
                    slug_hint = slug_hint or _extract_slug(detail_payload) or _normalize_slug_candidate(
                        detail_payload.get("urlName") or detail_payload.get("url")
                    )

                link_context = detail_payload or item
                source_link = _pick_best_link(session, link_context, slug_hint)

                if not media_url and source_link:
                    og_image = _extract_og_image(source_link, session)
                    media_url = _normalize_media_url(og_image) or media_url

                hint_texts = _collect_texts(
                    title,
                    description,
                    location_text_str,
                    venue_address_str,
                    item.get("genres"),
                )
                text_for_genre = " ".join(hint_texts)
                genres = detect_genres(text_for_genre, hints=hint_texts)

                if dedupe in seen_hashes:
                    continue

                existing = db.query(Event).filter_by(dedupe_hash=dedupe).first()
                if existing:
                    existing.title = title
                    existing.date = date
                    existing.time = time
                    existing.genres = genres
                    existing.venue = location_text_str or existing.venue
                    existing.city = city_str
                    existing.source_link = source_link
                    existing.media_url = media_url
                    if force_publish:
                        existing.status = "published"
                        existing.support_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
                    elif existing.status == "skipped":
                        existing.status = "queued"
                    updated += 1
                    continue

                ev = Event(
                    title=title,
                    title_norm=title_norm,
                    date=date,
                    time=time,
                    venue=location_text_str,
                    city=city_str,
                    genres=genres,
                    source_type="site",
                    source_name="venti",
                    source_link=source_link,
                    media_url=media_url,
                    dedupe_hash=dedupe,
                    status="published" if force_publish else "queued",
                    support_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8" if force_publish else None
                )
                db.add(ev)
                created += 1
        db.commit()
        print(f"[venti] Added {created} new events, updated {updated}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
