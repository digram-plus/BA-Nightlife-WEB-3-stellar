from fastapi import FastAPI, Depends, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from .db import SessionLocal
from .models import Event
from pydantic import BaseModel
import logging

# Import scrapers
from .scrapers import venti_parser, catpass_parser, passline_parser, bombo_parser

logger = logging.getLogger("api")

app = FastAPI(title="BA Nightlife API")

# --- CORS ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas for response
class EventSchema(BaseModel):
    id: int
    title: str
    date: date
    venue: Optional[str]
    genres: Optional[List[str]]
    source_link: Optional[str]
    media_url: Optional[str]
    support_wallet: Optional[str]
    vibe_description: Optional[str]

    class Config:
        from_attributes = True

class ScrapeResponse(BaseModel):
    message: str
    source: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/events", response_model=List[EventSchema])
def get_events(
    genre: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Event).filter(Event.status == "published")
    
    # User requested ONLY future events. Default to today if not specified.
    if start_date:
        query = query.filter(Event.date >= start_date)
    else:
        query = query.filter(Event.date >= date.today())
    
    if genre:
        query = query.filter(Event.genres.contains([genre]))
    
    return query.order_by(Event.date.asc()).all()

@app.get("/api/genres")
def get_genres(db: Session = Depends(get_db)):
    # Simple way to get unique genres from the ARRAY column
    events = db.query(Event.genres).filter(Event.genres != None).all()
    all_genres = set()
    for e in events:
        if e.genres:
            all_genres.update(e.genres)
    return sorted(list(all_genres))

def run_scraper_bg(source_name: str):
    logger.info(f"Triggering scraper: {source_name}")
    try:
        if source_name == "venti":
            venti_parser.run(limit=5, force_publish=True)
        elif source_name == "catpass":
            catpass_parser.run(limit=5, force_publish=True)
        elif source_name == "passline":
            passline_parser.run(limit=5, force_publish=True)
        elif source_name == "bombo":
            bombo_parser.run(limit=5, force_publish=True)
    except Exception as e:
        logger.error(f"Error running scraper {source_name}: {e}")

@app.post("/api/scrape/{source_name}", response_model=ScrapeResponse)
async def trigger_scrape(source_name: str, background_tasks: BackgroundTasks):
    valid_sources = ["venti", "catpass", "passline", "bombo"]
    if source_name not in valid_sources:
        raise HTTPException(status_code=400, detail="Invalid source")
    
    background_tasks.add_task(run_scraper_bg, source_name)
    
    return {"message": f"Scraper {source_name} started in background", "source": source_name}
