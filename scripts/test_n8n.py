import sys
import os
from datetime import date, time

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.n8n_service import push_event_to_n8n
from app.models import Event
from dotenv import load_dotenv

load_dotenv()

def main():
    print(f"Checking N8N_WEBHOOK_URL: {os.getenv('N8N_WEBHOOK_URL')}")
    
    # Create a dummy event
    dummy_event = Event(
        id=999999,
        title="Test Event for n8n",
        title_norm="test event for n8n",
        date=date.today(),
        time=time(22, 0),
        venue="Test Venue",
        genres=["Electronic", "Test"],
        source_link="https://example.com",
        media_url=None # Simulating missing image to test fallback
    )
    
    print("Pushing test event to n8n...")
    push_event_to_n8n(dummy_event)
    print("Done! Check your n8n interface.")

if __name__ == "__main__":
    main()
