# app/publisher/digest_publisher.py
import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT = Bot(token=os.getenv("TG_BOT_TOKEN"))
CHANNEL = os.getenv("TG_CHANNEL_ID")

def get_topic_id(genre: str) -> int:
    """Берёт ID темы из .env по ключу TOPIC_<GENRE>."""
    key = f"TOPIC_{genre.upper()}"
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Не найдено значение {key} в .env")
    return int(val)

async def send_digest(genre: str, text: str):
    """Отправляет текст в нужную тему по жанру."""
    topic_id = get_topic_id(genre)
    await BOT.send_message(
        chat_id=CHANNEL,
        message_thread_id=topic_id,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
