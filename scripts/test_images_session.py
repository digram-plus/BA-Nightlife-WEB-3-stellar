import asyncio
import os
import sys
from pathlib import Path

# Add root to sys.path
sys.path.append(os.getcwd())

from app.publisher.images import get_event_media
from app.models import Event
from datetime import date

async def test_session_cleanup():
    print("🚀 Testing aiohttp session cleanup in images.py")
    
    # Mock event
    ev = Event(
        title="Test Event",
        date=date.today(),
        media_url="https://images.unsplash.com/photo-1492684223066-81342ee5ff30?fm=jpg&q=80",
        genres=["Electronic"]
    )
    
    print("--- Fetching media (should use shared session internally) ---")
    media = await get_event_media(ev)
    
    if media:
        print("✅ Successfully fetched/generated media")
    else:
        print("❌ Failed to fetch/generate media")
    
    print("--- Test complete. Check if 'Unclosed client session' appears on exit ---")

if __name__ == "__main__":
    asyncio.run(test_session_cleanup())
