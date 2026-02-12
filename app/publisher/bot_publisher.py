import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot
from sqlalchemy.orm import Session
from aiogram.exceptions import TelegramRetryAfter
from ..db import SessionLocal
from ..models import Event
from ..config import Config
from ..utils import TZ
from .templates import build_caption, build_keyboard
from .images import get_event_media
from ..services.n8n_service import push_event_to_n8n

# ✅ настрой логирование
# ✅ настрой логирование
logging.basicConfig(
    filename='publisher.log',  # файл будет создаваться в корне проекта
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Инициализация Telegram-бота
BOT = Bot(token=os.getenv("TG_BOT_TOKEN"))
CHANNEL = os.getenv("TG_CHANNEL_ID")

TOPIC_PRIORITY = [
    "trance",
    "dnb",
    "techno",
    "house",
    "electronic",
    "rock",
    "pop",
    "indie",
    "metal",
    "rap",
    "jazz",
    "general",
]


def pick_topic(genres: list[str]) -> int:
    """Определяет тему для публикации по жанру."""
    normalized: list[str] = []
    for g in genres or []:
        g_key = (g or "").lower()
        if not g_key:
            continue
        if g_key == "misc":
            g_key = "general"
        if g_key not in normalized:
            normalized.append(g_key)
    if "general" not in normalized:
        normalized.append("general")

    for candidate in TOPIC_PRIORITY:
        if candidate in normalized:
            topic_id = Config.TOPIC_MAP.get(candidate)
            if topic_id:
                return topic_id

    for g_key in normalized:
        topic_id = Config.TOPIC_MAP.get(g_key)
        if topic_id:
            return topic_id
    return Config.TOPIC_MAP.get("general", 0)

async def publish_once(ev: Event):
    """Публикует одно событие в Telegram."""
    try:
        caption = build_caption(ev)
        kb = build_keyboard(ev)

        genres = getattr(ev, "genres", None) or []

        topic_id = pick_topic(genres)
        print(f"📤 Публикация '{ev.title}' → topic_id={topic_id}, status={ev.status}")

        if (
            Config.ENABLE_GENRE_ALERTS
            and Config.ADMIN_CHAT_ID
            and (not genres or all((g or "").lower() in ("general", "misc") for g in genres))
        ):
            try:
                date = getattr(ev, "date", None)
                time_obj = getattr(ev, "time", None)
                date_str = date.isoformat() if date else "—"
                time_str = time_obj.strftime("%H:%M") if time_obj else ""
                lines = [
                    f"⚠️ Не удалось определить жанр события",
                    f"{ev.title}",
                    f"Дата: {date_str} {time_str}".strip(),
                ]
                link = getattr(ev, "source_link", None) or getattr(ev, "source_url", None)
                if link:
                    lines.append(link)
                await BOT.send_message(
                    chat_id=Config.ADMIN_CHAT_ID,
                    text="\n".join(lines)
                )
            except Exception as alert_err:
                logging.warning("Не удалось отправить уведомление о жанре: %s", alert_err)

        media = await get_event_media(ev)
        msg = None
        for attempt in range(3):
            try:
                if media:
                    msg = await BOT.send_photo(
                        chat_id=CHANNEL,
                        photo=media,
                        caption=caption[:1024],
                        message_thread_id=topic_id if topic_id else None,
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                else:
                    msg = await BOT.send_message(
                        chat_id=CHANNEL,
                        text=caption[:4096],
                        message_thread_id=topic_id if topic_id else None,
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                break
            except TelegramRetryAfter as exc:
                wait_for = int(exc.retry_after) + 1
                print(f"⏳ Flood control, ждём {wait_for}s...")
                await asyncio.sleep(wait_for)
        if msg is None:
            raise RuntimeError("Не удалось отправить сообщение после повторных попыток.")

        print(f"✅ Опубликовано '{ev.title}' (msg_id={msg.message_id})")
        return msg.message_id, topic_id

    except Exception as e:
        print(f"⚠️ Ошибка при публикации '{getattr(ev, 'title', '?')}': {e}")
        import traceback
        traceback.print_exc()
        raise

async def run_publisher():
    """Основной цикл публикации очереди событий."""
    db: Session = SessionLocal()
    try:
        from datetime import timedelta
        # Fetch events within the 14-day horizon, filtered by city and retry status
        events = (
            db.query(Event)
            .filter(Event.status == "queued")
            .filter(Event.city == "Buenos Aires")
            .filter(Event.date >= today)
            .filter(Event.date <= horizon_date)
            .filter(
                (Event.next_retry_at == None) | (Event.next_retry_at <= datetime.now(TZ))
            )
            .order_by(Event.date.asc(), Event.id.asc())
            .limit(15)
            .all()
        )
    
        if not events:
            logging.info("No events within the 14-day horizon found.")
            return

        for ev in events:
            try:
                mid, tid = await publish_once(ev)
                ev.status = "published"
                ev.published_msg_id = mid
                ev.published_topic_id = tid
                db.commit()
                
                # Push to n8n after successful Telegram post to keep calendar/logs in sync
                try:
                    await push_event_to_n8n(ev)
                except Exception as n8n_err:
                    logging.warning(f"Failed to push {ev.title} to n8n: {n8n_err}")

                logging.info(f"Опубликовано '{ev.title}' (msg_id={mid}, topic_id={tid})")
                await asyncio.sleep(1.5)
            except Exception as e:
                ev.retry_count += 1
                if ev.retry_count > 5:
                    ev.status = "skipped"
                    logging.error(f"❌ '{ev.title}' окончательно пропущен после {ev.retry_count} попыток: {e}")
                else:
                    # Exponential backoff: 5m, 15m, 45m, 2h, 6h...
                    delay_minutes = 5 * (3 ** (ev.retry_count - 1))
                    ev.next_retry_at = datetime.now(TZ) + timedelta(minutes=delay_minutes)
                    logging.warning(f"⚠️ Ошибка публикации '{ev.title}' (попытка {ev.retry_count}): {e}. Следующая попытка через {delay_minutes} мин.")
                
                db.commit()

    finally:
        db.close()
