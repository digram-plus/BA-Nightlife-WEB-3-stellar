import os, asyncio
from telethon import TelegramClient
from sqlalchemy.orm import Session
from ..db import SessionLocal
from .query import pick_today_events
from .render import render_story

async def send_story():
    client = TelegramClient(os.getenv("TG_SESSION"), int(os.getenv("TG_API_ID")), os.getenv("TG_API_HASH"))
    async with client:
        db: Session = SessionLocal()
        events = pick_today_events(db, top_n=int(os.getenv("STORY_TOP_N", "3")))
        db.close()
        if not events:
            return
        png = render_story(events)
        png.name = "story.png"
        # Fallback: отправляем в топик календаря как обычный пост-картинку
        from aiogram import Bot
        bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
        await bot.send_photo(chat_id=os.getenv("TG_CHANNEL_ID"), photo=png, caption="Hoy en BA — selección del día", message_thread_id=int(os.getenv("TOPIC_GENERAL","0")))
