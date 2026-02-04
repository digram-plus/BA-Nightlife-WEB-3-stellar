import asyncio
import os
from aiogram import Bot
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Event
from app.config import Config

async def cleanup():
    bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
    channel_id = os.getenv("TG_CHANNEL_ID")
    db: Session = SessionLocal()
    
    events = db.query(Event).filter(Event.published_msg_id != None).all()
    print(f"Found {len(events)} published events to delete.")
    
    for ev in events:
        try:
            await bot.delete_message(chat_id=channel_id, message_id=ev.published_msg_id)
            print(f"Deleted message {ev.published_msg_id} for event {ev.title}")
        except Exception as e:
            print(f"Could not delete message {ev.published_msg_id}: {e}")
        await asyncio.sleep(0.1) # Avoid rate limits
        
    # Now clear the DB
    try:
        db.query(Event).delete()
        db.commit()
        print("Database cleared.")
    except Exception as e:
        print(f"Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(cleanup())
