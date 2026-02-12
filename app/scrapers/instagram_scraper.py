import os
import logging
from datetime import datetime, timedelta
import instaloader
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import normalize_title, make_hash, parse_date
from ..services.n8n_service import push_event_to_n8n

logger = logging.getLogger("instagram_scraper")
logging.basicConfig(level=logging.INFO)

def run(limit: int = 10, force_publish: bool = False):
    profiles = (os.getenv("INSTAGRAM_PROFILES") or "").split(",")
    profiles = [p.strip() for p in profiles if p.strip()]
    if not profiles:
        logger.warning("No INSTAGRAM_PROFILES set in .env")
        return

    L = instaloader.Instaloader()
    
    # Optional login
    user = os.getenv("INSTAGRAM_USER")
    password = os.getenv("INSTAGRAM_PASSWORD")
    if user and password:
        try:
            L.login(user, password)
            logger.info(f"Logged in as {user}")
        except Exception as e:
            logger.error(f"Failed to login to Instagram: {e}")

    db: Session = SessionLocal()
    created = 0
    
    try:
        for profile_name in profiles:
            logger.info(f"Scraping Instagram profile: {profile_name}")
            try:
                profile = instaloader.Profile.from_username(L.context, profile_name)
                posts = profile.get_posts()
                
                count = 0
                for post in posts:
                    if count >= limit:
                        break
                    
                    # Only look at recent posts (last 7 days)
                    if post.date_utc < datetime.utcnow() - timedelta(days=7):
                        break

                    caption = post.caption or ""
                    if not caption:
                        continue

                    date_obj, time_obj = parse_date(caption)
                    if not date_obj:
                        continue

                    title = caption.split("\n", 1)[0][:200]
                    title_norm = normalize_title(title)
                    dedupe = make_hash(title_norm, date_obj.isoformat(), profile_name)

                    existing = db.query(Event).filter_by(dedupe_hash=dedupe).first()
                    if existing:
                        continue

                    genres, artists = detect_genres(caption, hints=[title, profile_name])
                    
                    ev = Event(
                        title=title,
                        title_norm=title_norm,
                        date=date_obj,
                        time=time_obj,
                        venue=profile_name, # Fallback
                        genres=genres,
                        artists=artists,
                        source_type="instagram",
                        source_name=profile_name,
                        source_link=f"https://www.instagram.com/p/{post.shortcode}/",
                        media_url=post.url,
                        dedupe_hash=dedupe,
                        status="published" if force_publish else "queued",
                    )
                    db.add(ev)
                    db.flush()
                    created += 1
                    count += 1
                    
            except Exception as e:
                logger.error(f"Error scraping {profile_name}: {e}")
                
        db.commit()
        logger.info(f"Instagram scraper finished. Added {created} events.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
