import asyncio
import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional, cast

from telethon import TelegramClient
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import normalize_title, make_hash, parse_date
from ..services.ocr import extract_text_from_bytes
# from ..services.n8n_service import push_event_to_n8n

DEFAULT_CHANNELS = [
    "AfishaBA",
    "vista_argentina",
    "buenosaires_afisha",
    "TechnoLoversBA",
    "eventosbsas",
    "v3underground",
    "technoargentina",
    "house_music_ba",
    "raves_ba",
    "electronic_ba",
    "underground_ba",
]


def _load_channels() -> list[str]:
    raw = (os.getenv("TG_CHANNELS") or "").strip()
    if not raw:
        return DEFAULT_CHANNELS
    channels: list[str] = []
    for item in raw.split(","):
        name = item.strip()
        if not name:
            continue
        if name.startswith("@"):
            name = name[1:]
        channels.append(name)
    return channels or DEFAULT_CHANNELS

IMAGE_MIME_PREFIX = "image/"


def _is_image_message(msg) -> bool:
    if msg.photo:
        return True
    doc = getattr(msg, "document", None)
    mime = getattr(doc, "mime_type", "") if doc else ""
    return bool(mime and mime.startswith(IMAGE_MIME_PREFIX))


async def _extract_media_text(msg) -> str:
    if not _is_image_message(msg):
        return ""
    try:
        buffer = BytesIO()
        data = await msg.download_media(file=buffer)
        if isinstance(data, BytesIO):
            raw = data.getvalue()
        elif isinstance(data, bytes):
            raw = data
        else:
            raw = buffer.getvalue()
        return extract_text_from_bytes(raw) if raw else ""
    except Exception:
        return ""


async def fetch_and_store(limit: Optional[int] = None, force_publish: bool = False):
    api_id_raw = os.getenv("TG_API_ID")
    api_hash_raw = os.getenv("TG_API_HASH")
    session_name_raw = os.getenv("TG_SESSION")
    if not api_id_raw or not api_hash_raw or not session_name_raw:
        print("Missing TG_API_ID/TG_API_HASH/TG_SESSION")
        return

    api_id = int(cast(str, api_id_raw))
    api_hash = cast(str, api_hash_raw)
    session_name = cast(str, session_name_raw)

    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        await client.connect()
    except Exception as e:
        if "database is locked" in str(e).lower():
            print(f"⚠️ Session '{session_name}' is locked by another process. Trying temporary session...")
            temp_session = f"{session_name}_tmp_{os.getpid()}"
            client = TelegramClient(temp_session, api_id, api_hash)
            await client.start() # This might require phone/code if not logged in
        else:
            raise e

    async with client:
        db: Session = SessionLocal()
        created = 0
        try:
            all_found_events = []
            for ch in _load_channels():
                cutoff = None
                if os.getenv("TG_LOOKBACK_DAYS"):
                    try:
                        days = int(os.getenv("TG_LOOKBACK_DAYS", "0"))
                        if days > 0:
                            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                    except ValueError:
                        pass

                print(f"[telegram] Checking channel: {ch}")
                async for msg in client.iter_messages(ch, limit=100):
                    if cutoff and getattr(msg, "date", None):
                        msg_date = msg.date
                        if msg_date.tzinfo is None:
                            msg_date = msg_date.replace(tzinfo=timezone.utc)
                        if msg_date < cutoff:
                            break # stop if we reached the cutoff

                    text = (msg.text or msg.message or "").strip()
                    if not text and not _is_image_message(msg):
                        continue

                    # Rough parse for sorting
                    date_val, time_val = parse_date(text) if text else (None, None)
                    
                    all_found_events.append({
                        "msg": msg,
                        "ch": ch,
                        "date": date_val,
                        "time": time_val,
                        "text": text
                    })
            
            # Filter and sort
            all_found_events = [e for e in all_found_events if e["date"]]
            all_found_events.sort(key=lambda x: x["date"])
            
            if limit:
                all_found_events = all_found_events[:limit]
            
            print(f"[telegram] Processing top {len(all_found_events)} upcoming events")

            for item in all_found_events:
                msg = item["msg"]
                ch = item["ch"]
                date = item["date"]
                time = item["time"]
                text = item["text"]
                
                media_text = ""
                if not date and _is_image_message(msg): # Should not happen with current filter but for future proof
                    media_text = await _extract_media_text(msg)

                combined_text = " ".join(part for part in (text, media_text) if part)
                if not combined_text:
                    continue

                if not date: # Fallback if first parse failed or we have media text now
                    date, time = parse_date(combined_text)
                    if not date:
                        continue

                base_title = text if text else media_text
                if not base_title:
                    continue
                title = base_title.split("\n", 1)[0][:280]

                title_norm = normalize_title(title)
                h = make_hash(title_norm, date.isoformat(), None)
                
                existing = db.query(Event).filter_by(dedupe_hash=h).first()
                if existing:
                    if force_publish:
                        existing.status = "published"
                        existing.support_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
                    continue

                genres = detect_genres(combined_text, hints=[title, ch, media_text])
                ev = Event(
                    title=title,
                    title_norm=title_norm,
                    date=date,
                    time=time,
                    venue=None,
                    genres=genres,
                    source_type="telegram",
                    source_name=ch,
                    source_link=f"https://t.me/{ch}/{msg.id}",
                    source_msg_id=msg.id,
                    media_url=None,
                    dedupe_hash=h,
                    support_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
                )
                db.add(ev)
                db.flush() 
                # push_event_to_n8n(ev)
                created += 1
            db.commit()
        finally:
            db.close()
