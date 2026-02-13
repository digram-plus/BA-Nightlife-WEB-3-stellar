import asyncio
import os
import logging
from datetime import datetime, timedelta
from app.publisher.bot_publisher import publish_once
from app.models import Event
from app.db import SessionLocal
from app.utils import TZ
from app.services.n8n_service import push_event_to_n8n

async def run_limited():
    db = SessionLocal()
    try:
        today = datetime.now(TZ).date()
        horizon = today + timedelta(days=14)
        events = db.query(Event).filter(
            Event.status == "queued",
            Event.city == "Buenos Aires",
            Event.date >= today,
            Event.date <= horizon
        ).order_by(Event.date.asc(), Event.id.asc()).limit(5).all()

        print(f"Queue: {len(events)} events found.")
        
        for ev in events:
            try:
                mid, tid = await publish_once(ev)
                ev.status = "published"
                ev.published_msg_id = mid
                ev.published_topic_id = tid
                db.commit()
                # Push to n8n
                try:
                    await push_event_to_n8n(ev)
                except Exception as n8n_err:
                    print(f"n8n error: {n8n_err}")
                
                print(f"✅ Published: {ev.title}")
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"❌ Error publishing {ev.title}: {e}")
                db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_limited())
