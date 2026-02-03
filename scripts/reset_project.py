import asyncio
import os
import sys
from aiogram import Bot
from sqlalchemy import text
from app.db import SessionLocal
from app.models import Event, CheckIn
from dotenv import load_dotenv

load_dotenv()

async def reset_project():
    print("🚀 Starting full project reset...")
    
    db = SessionLocal()
    bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
    channel_id = os.getenv("TG_CHANNEL_ID")

    try:
        # 1. Get all events with published_msg_id
        events_with_posts = db.query(Event).filter(Event.published_msg_id != None).all()
        print(f"📦 Found {len(events_with_posts)} posts to potentially delete from Telegram.")

        # 2. Try to delete posts from Telegram
        for ev in events_with_posts:
            try:
                await bot.delete_message(chat_id=channel_id, message_id=ev.published_msg_id)
                print(f"  ✅ Deleted post for '{ev.title}' (ID: {ev.published_msg_id})")
            except Exception as e:
                print(f"  ⚠️ Could not delete post for '{ev.title}': {e} (might be older than 48h)")

        # 3. Wipe database
        print("💾 Wiping database tables...")
        db.query(CheckIn).delete()
        db.query(Event).delete()
        db.commit()
        print("✅ Database wiped successfully.")

    except Exception as e:
        print(f"❌ Error during reset: {e}")
        db.rollback()
    finally:
        db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(reset_project())
