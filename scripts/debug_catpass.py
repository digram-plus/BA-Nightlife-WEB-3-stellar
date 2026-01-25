import sys
import os
from datetime import date

# Add app to path
sys.path.append(os.getcwd())

from app.db import SessionLocal
from app.models import Event

def inspect_events():
    db = SessionLocal()
    print(f"--- Checking Events (Today: {date.today()}) ---")
    
    # Check Catpass
    query = db.query(Event).filter(Event.source_name == 'catpass')
    events = query.all()
    print(f"\nFound {len(events)} Catpass events:")
    for e in events:
        print(f"[ID: {e.id}] {e.title}")
        print(f"  Date: {e.date} (Type: {type(e.date)})")
        print(f"  Status: {e.status}")
        print(f"  Hash: {e.dedupe_hash}")
        print(f"  Media: {e.media_url}")
        print("-" * 20)

    # Check Venti just for comparison
    v_count = db.query(Event).filter(Event.source_name == 'venti', Event.status == 'published').count()
    print(f"\nTotal Published Venti Events: {v_count}")

    db.close()

if __name__ == "__main__":
    inspect_events()
