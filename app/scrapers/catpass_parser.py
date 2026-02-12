import logging
import requests
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import (
    TZ,
    make_hash,
    normalize_title,
    parse_date,
    detect_city,
)
# from ..services.n8n_service import push_event_to_n8n


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("catpass")

API_URL = "https://catpass-production.up.railway.app/eventos"
SITE_BASE = "https://catpass.net"


def _parse_datetime(fecha: Optional[str], hora: Optional[str]):
    if fecha:
        try:
            dt = datetime.fromisoformat(fecha)
            dt = dt.astimezone(TZ).replace(tzinfo=None)
            date = dt.date()
        except Exception:
            date = None
    else:
        date = None

    if hora and len(hora) <= 5 and ":" in hora:
        try:
            t = datetime.strptime(hora, "%H:%M").time()
        except Exception:
            t = None
    else:
        t = None

    return date, t


def run(limit: int = None, force_publish: bool = False):
    logger.info("[catpass] Fetching events…")
    try:
        resp = requests.get(API_URL, timeout=20)
        resp.raise_for_status()
        events_payload = resp.json()
        if not isinstance(events_payload, list):
            logger.warning("[catpass] Unexpected payload format")
            return
    except Exception as exc:
        logger.error(f"[catpass] Failed to fetch API: {exc}")
        return

    # Collect and sort items by date before processing
    items_with_dates = []
    for item in events_payload:
        if not isinstance(item, dict):
            continue
        fecha = item.get("fecha")
        hora = item.get("hora")
        date, time = _parse_datetime(fecha, hora) # Keep using _parse_datetime as parse_date from utils returns datetime object, not date, time tuple.
        if date:
            items_with_dates.append((date, time, item))
    
    # Sort by date
    items_with_dates.sort(key=lambda x: x[0])
    
    if limit:
        items_with_dates = items_with_dates[:limit]

    db: Session = SessionLocal()
    created = 0
    updated = 0
    try:
        for date, time, item in items_with_dates:
            title = item.get("nombre")
            if not title:
                continue

            descripcion = item.get("descripcion") or ""
            # date, time already parsed during sorting

            venue = item.get("ubicacion") or None
            title_norm = normalize_title(title)
            dedupe = make_hash(title_norm, date.isoformat(), venue)

            slug = item.get("slug")
            if slug:
                source_link = f"{SITE_BASE}/evento/{slug}"
            else:
                source_link = SITE_BASE

            media_url = item.get("img") or None

            combined_text = " ".join(filter(None, [title, descripcion, venue]))
            genres, artists = detect_genres(title, hints=[descripcion, venue])

            existing = db.query(Event).filter_by(dedupe_hash=dedupe).first()
            if existing:
                existing.title = title
                existing.date = date
                existing.time = time
                existing.genres = genres
                existing.artists = artists
                existing.venue = venue or existing.venue
                existing.source_link = source_link
                existing.media_url = media_url
                if force_publish:
                    existing.status = "published"
                    existing.support_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
                    # push_event_to_n8n(existing)
                elif existing.status == "skipped":
                    existing.status = "queued"
                updated += 1
                continue

            ev = Event(
                title=title,
                title_norm=title_norm,
                date=date,
                time=time,
                venue=venue,
                city=detect_city(" ".join(filter(None, [venue, title]))),
                genres=genres,
                artists=artists,
                source_type="site",
                source_name="catpass",
                source_link=source_link,
                media_url=media_url,
                dedupe_hash=dedupe,
                status="published" if force_publish else "queued",
                support_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8" if force_publish else None
            )
            db.add(ev)
            db.flush()
            # push_event_to_n8n(ev)
            created += 1

        db.commit()
        logger.info(f"[catpass] Added {created} new events, updated {updated}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
