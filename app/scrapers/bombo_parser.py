import logging
import requests
import cloudscraper
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from urllib.parse import urljoin

from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import normalize_title, make_hash, parse_date
from ..services.ocr import extract_text
from .link_utils import resolve_canonical_url
# from ..services.n8n_service import push_event_to_n8n

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bombo")

PAGE_URL = "https://wearebombo.com/wp-json/wp/v2/pages/991304"
BASE_SITE = "https://wearebombo.com/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://wearebombo.com/",
}


def _collect_slides(soup: BeautifulSoup):
    heading = soup.find(lambda tag: tag.name in ("h2", "h3") and "eventos" in tag.get_text(strip=True).lower())
    if not heading:
        return []

    carousel = heading.find_next(lambda tag: tag.name == "div" and tag.get("data-widget_type") == "eael-post-carousel.default")
    if not carousel:
        return []

    return carousel.select(".swiper-slide")


def run(limit: int = None, force_publish: bool = False):
    logger.info("[bombo] Fetching events…")
    # Use cloudscraper to bypass potential 403/401 WAFs
    scraper = cloudscraper.create_scraper()
    scraper.headers.update(HEADERS)
    
    try:
        resp = scraper.get(PAGE_URL, timeout=20)
        resp.raise_for_status()
        content_html = resp.json()["content"]["rendered"]
    except Exception as exc:
        logger.error(f"[bombo] Failed to fetch page: {exc}")
        return

    soup = BeautifulSoup(content_html, "html.parser")
    slides = _collect_slides(soup)
    if not slides:
        logger.warning("[bombo] No slides found on the page.")
        return

    db: Session = SessionLocal()
    created = 0
    updated = 0
    try:
    # Collect and sort slides by date before processing
    slides_with_dates = []
    for slide in slides:
        title_el = slide.select_one(".eael-entry-title")
        time_el = slide.select_one("time")
        if not title_el or not time_el:
            continue
            
        title = title_el.get_text(strip=True)
        date_str = time_el.get("datetime") or time_el.get_text(" ", strip=True)
        
        img_el = slide.select_one(".eael-entry-thumbnail img")
        media_url = img_el.get("src") if img_el else None
        meta_text = slide.get_text(" ", strip=True)
        
        # We need a rough date for sorting. Bombo usually lists events in order,
        # but let's try to parse for safety.
        # Note: parse_date might be slow if it uses LLM or OCR, so we'll 
        # try to use just the date_str if available.
        dt, tm = parse_date(date_str)
        if dt:
            slides_with_dates.append((dt, tm, slide, title, media_url, meta_text, date_str))
    
    # Sort by date
    slides_with_dates.sort(key=lambda x: x[0])
    
    if limit:
        slides_with_dates = slides_with_dates[:limit]

    db: Session = SessionLocal()
    created = 0
    updated = 0
    try:
        for dt, tm, slide, title, media_url, meta_text, date_str in slides_with_dates:
            link_el = slide.select_one(".eael-grid-post-link")
            link = link_el.get("href") if link_el else None
            # ... rest of processing

            title_norm = normalize_title(title)
            dedupe = make_hash(title_norm, dt.isoformat(), None)

            genres = detect_genres(combined_text, hints=[title, meta_text, ocr_text])

            existing = db.query(Event).filter_by(dedupe_hash=dedupe).first()
            if existing:
                existing.title = title
                existing.date = dt
                existing.time = tm
                existing.media_url = media_url
                existing.source_link = source_link
                existing.genres = genres
                if force_publish:
                    existing.status = "published"
                    existing.support_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8" # Demo wallet
                    # push_event_to_n8n(existing)
                elif existing.status == "skipped":
                    existing.status = "queued"
                updated += 1
                continue

            ev = Event(
                title=title,
                title_norm=title_norm,
                date=dt,
                time=tm,
                venue=None,
                city="Buenos Aires",
                genres=genres,
                source_type="site",
                source_name="bombo",
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
        logger.info(f"[bombo] Added {created} new events, updated {updated}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
