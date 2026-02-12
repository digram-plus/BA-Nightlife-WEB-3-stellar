import logging
import requests
import re
import os
from datetime import datetime, time, date as ddate
from urllib.parse import urljoin

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

from bs4 import BeautifulSoup
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
logger = logging.getLogger("passline")

URL = "https://www.passline.com/sitio/argentina"

MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12
}

def _parse_passline_date_time(date_div, time_div):
    """
    Parses Passline's specific date/time structure.
    Date Div contains: Day (21) and MonthYear (Ene 2026)
    Time Div contains: Hour (10) and MinUnits (00 hrs)
    """
    event_date = None
    event_time = None
    
    try:
        # Date
        if date_div:
            day_str = date_div.select_one(".fs-2").get_text(strip=True)
            month_year_block = date_div.select_one("span:nth-of-type(2)").get_text(" ", strip=True)
            # month_year_block might be "Ene 2026" or "Ene\n2026"
            parts = month_year_block.split()
            if len(parts) >= 2:
                month_str = parts[0].lower().replace(".", "")
                year_str = parts[1]
                month = MONTHS_ES.get(month_str, 1)
                event_date = ddate(int(year_str), month, int(day_str))
    except Exception as e:
        logger.warning(f"Error parsing date: {e}")

    try:
        # Time
        if time_div:
            hour_str = time_div.select_one(".fs-2").get_text(strip=True)
            min_block = time_div.select_one("span:nth-of-type(2)").get_text(" ", strip=True)
            # min_block might be "00 hrs"
            min_str = re.sub(r"[^\d]", "", min_block)
            if not min_str: 
                min_str = "00"
            event_time = time(int(hour_str), int(min_str))
    except Exception as e:
        logger.warning(f"Error parsing time: {e}")

    return event_date, event_time

def run(limit: int = None, force_publish: bool = False):
    logger.info(f"[passline] Fetching events from {URL} ...")
    
    html = None
    try:
        if cloudscraper:
             session = cloudscraper.create_scraper()
             resp = session.get(URL, timeout=30)
        else:
             session = requests.Session()
             resp = session.get(URL, timeout=30)
             
        resp.raise_for_status()
        html = resp.text
        
        # Cloudflare check
        if "Just a moment" in html or len(html) < 15000:
            logger.warning("[passline] Cloudflare challenge detected. Fetch might be incomplete.")
            html = None # Trigger fallback
        
    except Exception as exc:
        logger.error(f"[passline] Failed to fetch page: {exc}")
        
    # Local Fallback
    fallback_file = "Passline - Líder en venta de entradas para eventos.html"
    if not html and os.path.exists(fallback_file):
        logger.info(f"[passline] Using local fallback file: {fallback_file}")
        with open(fallback_file, "r", encoding="utf-8") as f:
            html = f.read()

    if not html:
        logger.error("[passline] No HTML content available (Network failed and no local backup).")
        return

    soup = BeautifulSoup(html, "html.parser")
    # Selection logic verified with local file
    cards = soup.select("div.card.d-none.d-md-block")
    
    if not cards:
        logger.info("[passline] No cards found with desktop selector. Checking mobile.")
        cards = soup.select("div.card")

    if not cards:
        logger.warning("[passline] No cards found on the page.")
        return

    logger.info(f"[passline] Found {len(cards)} cards on the page.")

    # Sort cards by date before processing
    card_with_dates = []
    for item in cards:
        date_div = item.select_one("div.event-date")
        time_div = item.select_one("div.event-hours")
        date_obj, time_obj = _parse_passline_date_time(date_div, time_div)
        if date_obj:
            card_with_dates.append((date_obj, time_obj, item))
    
    # Sort by date
    card_with_dates.sort(key=lambda x: x[0])
    
    if limit:
        card_with_dates = card_with_dates[:limit]

    db: Session = SessionLocal()
    created = 0
    updated = 0
    
    try:
        for date_obj, time_obj, item in card_with_dates:
            # 1. Title
            title_el = item.select_one("p.card-title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            
            # 2. Link
            link_el = item.select_one("a")
            if not link_el or not link_el.get("href"):
                continue
            source_link = link_el["href"]
            if not source_link.startswith("http"):
                source_link = urljoin(URL, source_link)

            # 3. Venue
            venue_el = item.select_one("small.card-location")
            venue_text = venue_el.get_text(strip=True) if venue_el else "Buenos Aires"

            # 4. Date & Time (already parsed during sorting)
            if not date_obj:
                continue

            # 5. Image
            img_el = item.select_one("img")
            media_url = None
            if img_el:
                raw_src = img_el.get("src") or img_el.get("data-src")
                if raw_src:
                     if raw_src.startswith("http"):
                         media_url = raw_src
                     else:
                         media_url = urljoin(URL, raw_src)

            title_norm = normalize_title(title)
            dedupe = make_hash(title_norm, date_obj.isoformat(), venue_text)
            
            genres, artists = detect_genres(title, hints=[venue_text])

            existing = db.query(Event).filter_by(dedupe_hash=dedupe).first()
            if existing:
                existing.source_link = source_link
                existing.media_url = media_url if media_url else existing.media_url
                existing.time = time_obj or existing.time
                existing.genres = genres
                existing.artists = artists
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
                date=date_obj,
                time=time_obj,
                venue=venue_text,
                city=detect_city(" ".join(filter(None, [venue_text, title]))),
                genres=genres,
                artists=artists,
                source_type="site",
                source_name="passline",
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
        logger.info(f"[passline] Finished. Added {created} new events, updated {updated}.")

    finally:
        db.close()

if __name__ == "__main__":
    run()
