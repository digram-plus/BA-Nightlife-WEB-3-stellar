import httpx
import os
import logging
from urllib.parse import quote
from ..models import Event

logger = logging.getLogger("n8n_service")

async def push_event_to_n8n(event: Event):
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
    if not N8N_WEBHOOK_URL:
        logger.warning("N8N_WEBHOOK_URL is not set")
        return
    
    # Format helpers for n8n
    event_datetime = str(event.date)
    if event.time:
        event_datetime = f"{event.date} {event.time}"
    
    primary_genre = event.genres[0] if event.genres and len(event.genres) > 0 else "electronic"

    # Image Fallback
    DEFAULT_IMAGE = "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?fm=jpg&q=80" 
    final_image_url = event.media_url if event.media_url else DEFAULT_IMAGE

    # Generate YouTube Music Link
    search_query = quote(event.title)
    youtube_music_url = f"https://music.youtube.com/search?q={search_query}"

    payload = {
        "id": event.id,
        "title": event.title,
        "date": str(event.date),
        "time": str(event.time) if event.time else None,
        "venue": event.venue,
        "genres": event.genres,
        "source_link": event.source_link,
        "media_url": event.media_url,
        "event_title": event.title,
        "event_datetime": event_datetime,
        "primary_genre": primary_genre,
        "final_image_url": final_image_url,
        "youtube_music_url": youtube_music_url,
        "topic_id": event.published_topic_id
    }
    
    logger.info(f"[n8n] Pushing event '{event.title}' to n8n...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(N8N_WEBHOOK_URL, json=payload)
            logger.info(f"[n8n] Result for '{event.title}': Status {response.status_code}")
            if response.status_code != 200:
                logger.error(f"[n8n] Error Response: {response.text}")
            response.raise_for_status()
    except Exception as e:
        logger.error(f"[n8n] CRITICAL Error pushing event '{event.title}': {e}")
