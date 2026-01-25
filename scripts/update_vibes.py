
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Event
from app.config import Config

# DB Setup - Sync
# Assuming Config.POSTGRES_... are set correctly
DATABASE_URL = f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

VIBE_TEMPLATES = {
    "techno": [
        "🌑 Dark, industrial warehouse energy. Prepare for pounding kick drums.",
        "🔨 Hard hitting rhythms and hypnotic loops. Strictly for the heads.",
        "🌩️ Thunderous basslines and strobe lights. Lose yourself in the music.",
    ],
    "house": [
        "✨ Uplifting vocals and groovy basslines. Perfect for cocktails and dancing.",
        "💃 Soulful vibes and infectious energy. Bringing the Ibiza heat to BA.",
        "🪩 Disco balls and funky rhythms. A night of pure euphoria.",
    ],
    "trance": [
        "🌌 Ethereal melodies and high BPMs. A journey to another dimension.",
        "🚀 Euphoric drops and hands-in-the-air moments. Pure energy.",
    ],
    "cumbia": [
        "🌴 Tropical heat and infectious rhythm. Imposible no bailar.",
        "🔥 The real sound of the barrio. Sweat, dance, and passion.",
    ],
    "rock": [
        "🎸 Shredding guitars and raw power. Moshing encouraged.",
        "🤘 Live energy and classic anthems. A night of pure rock 'n' roll.",
    ],
    "pop": [
        "🎤 Sing-along anthems and glitter. The ultimate party vibe.",
        "🍬 Sweet melodies and chart-toppers. Bring your best moves.",
    ],
    "general": [
        "🔥 The hottest ticket in town. Expect a packed crowd.",
        "👀 The event everyone is talking about. See and be seen.",
        "⚡ A unique experience in the heart of the city.",
    ]
}

def get_vibe(title: str, genres: list[str]) -> str:
    text = (title + " " + " ".join(genres or [])).lower()
    
    if "techno" in text or "hard" in text:
        return random.choice(VIBE_TEMPLATES["techno"])
    if "house" in text or "disco" in text:
        return random.choice(VIBE_TEMPLATES["house"])
    if "trance" in text or "psy" in text:
         return random.choice(VIBE_TEMPLATES["trance"])
    if "cumbia" in text or "reggaeton" in text or "latino" in text:
        return random.choice(VIBE_TEMPLATES["cumbia"])
    if "rock" in text or "indie" in text or "metal" in text:
        return random.choice(VIBE_TEMPLATES["rock"])
    if "pop" in text or "hits" in text:
        return random.choice(VIBE_TEMPLATES["pop"])
        
    return random.choice(VIBE_TEMPLATES["general"])

def main():
    session = SessionLocal()
    try:
        # Get all future/recent events
        events = session.query(Event).filter(Event.date >= '2025-01-01').all()
        
        print(f"Found {len(events)} events to vibe check...")
        
        count = 0
        for event in events:
            # Generate and assign vibe
            vibe = get_vibe(event.title, event.genres)
            event.vibe_description = vibe
            count += 1
            print(f"Vibe checked: {event.title[:30]}... -> {vibe}")
            
        session.commit()
        print(f"Updated {count} events with fresh vibes 🌊")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
