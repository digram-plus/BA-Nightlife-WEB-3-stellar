import os
import logging
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db import SessionLocal
from app.models import Event
from app.utils import detect_city

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix_cities")

load_dotenv()

def main():
    db: Session = SessionLocal()
    try:
        # Fetch all events (or we could limit to only recent ones)
        events = db.query(Event).all()
        logger.info(f"Checking {len(events)} events...")
        
        fixed_count = 0
        skipped_count = 0
        
        for ev in events:
            # Combine all available text for city detection
            text_to_scan = " ".join(filter(None, [
                ev.title,
                ev.venue,
                ev.vibe_description
            ]))
            
            new_city = detect_city(text_to_scan)
            
            if ev.city != new_city:
                logger.info(f"Fixing '{ev.title}': {ev.city} -> {new_city}")
                ev.city = new_city
                
                # Optional: Re-queue if it was incorrectly labeled but not yet published
                # Or even "unpublish" if it was published to a general channel but isn't for BA
                # Given the user's request, we just want to fix the mapping first.
                
                fixed_count += 1
            else:
                skipped_count += 1
        
        db.commit()
        logger.info(f"Finished! Fixed: {fixed_count}, Skipped: {skipped_count}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
