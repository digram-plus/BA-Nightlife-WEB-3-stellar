import requests
import os
from urllib.parse import quote
from ..models import Event


def push_event_to_n8n(event: Event):
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
    if not N8N_WEBHOOK_URL:
        print("N8N_WEBHOOK_URL is not set")
        return
    
    
    # Format helpers for n8n
    event_datetime = str(event.date)
    if event.time:
        event_datetime = f"{event.date} {event.time}"
    
    primary_genre = event.genres[0] if event.genres and len(event.genres) > 0 else "Electronic"

    # Image Fallback
    # Using a generic "Nightlife" placeholder if media_url is missing
    # Added ?fm=jpg to ensure it serves an image content-type
    DEFAULT_IMAGE = "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?fm=jpg&q=80" 
    final_image_url = event.media_url if event.media_url else DEFAULT_IMAGE

    # Generate YouTube Music Link
    # Searching by title. Ideally, we'd search by "Artist - Title", but title often contains both.
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
        # Formatted fields for n8n message template
        "event_title": event.title,
        "event_datetime": event_datetime,
        "primary_genre": primary_genre,
        "final_image_url": final_image_url,
        "youtube_music_url": youtube_music_url
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        response.raise_for_status()
    except Exception as e:
        print(f"Error pushing event to n8n: {e}")
