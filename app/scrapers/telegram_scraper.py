import asyncio
import os
from io import BytesIO

from telethon import TelegramClient
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import normalize_title, make_hash, parse_date
from ..services.ocr import extract_text_from_bytes
from ..services.n8n_service import push_event_to_n8n

CHANNELS = ["AfishaBA", "vista_argentina", "buenosaires_afisha"]

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


async def fetch_and_store(limit: int = None, force_publish: bool = False):
    client = TelegramClient(os.getenv("TG_SESSION"), int(os.getenv("TG_API_ID")), os.getenv("TG_API_HASH"))
    async with client:
        db: Session = SessionLocal()
        created = 0
        try:
            for ch in CHANNELS:
                if limit and created >= limit:
                    break
                entity = await client.get_entity(ch)
                async for msg in client.iter_messages(entity, limit=50):
                    if limit and created >= limit:
                        break
                        
                    text = (msg.text or msg.message or "").strip()
                    media_text = await _extract_media_text(msg)
                    combined_text = " ".join(part for part in (text, media_text) if part)
                    if not combined_text:
                        continue

                    base_title = text if text else media_text
                    if not base_title:
                        continue
                    title = base_title.split("\n", 1)[0][:280]

                    date, time = parse_date(combined_text)
                    if not date:
                        continue

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
                        status="published" if force_publish else "queued",
                        dedupe_hash=h,
                        support_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8" if force_publish else None
                    )
                    db.add(ev)
                    db.flush() # Generate ID
                    push_event_to_n8n(ev)
                    created += 1
            db.commit()
        finally:
            db.close()
