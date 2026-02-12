import os
import httpx
from dotenv import load_dotenv
import secrets
from pathlib import Path
from datetime import date, datetime
from fastapi import FastAPI, Depends, Query, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from eth_account import Account
from eth_account.messages import encode_defunct
from .db import SessionLocal
from .models import Event, CheckIn
from pydantic import BaseModel
import logging

# Import scrapers
from .scrapers import venti_parser, catpass_parser, passline_parser, bombo_parser

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger("api")

SCRAPE_API_KEY = os.getenv("SCRAPE_API_KEY")
OPENFORT_SHIELD_SECRET_KEY = os.getenv("OPENFORT_SHIELD_SECRET_KEY")
OPENFORT_SHIELD_ENCRYPTION_SHARE = os.getenv("OPENFORT_SHIELD_ENCRYPTION_SHARE")
NEXT_PUBLIC_SHIELD_PUBLISHABLE_KEY = os.getenv("NEXT_PUBLIC_SHIELD_PUBLISHABLE_KEY")

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


class CheckInChallengeRequest(BaseModel):
    event_id: int


class CheckInChallengeResponse(BaseModel):
    event_id: int
    nonce: str
    message: str


class CheckInVerifyRequest(BaseModel):
    event_id: int
    wallet_address: str
    signature: str
    message: str
    nonce: str


class CheckInVerifyResponse(BaseModel):
    status: str
    checkin_id: int
    created_at: datetime


class CheckInStatusResponse(BaseModel):
    status: str
    checkin_id: Optional[int] = None
    created_at: Optional[datetime] = None

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_scrape_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if not SCRAPE_API_KEY:
        raise HTTPException(status_code=500, detail="SCRAPE_API_KEY not configured")
    if not x_api_key or x_api_key != SCRAPE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def build_checkin_message(event_id: int, event_date: date, nonce: str) -> str:
    return "\n".join(
        [
            "BA Nightlife Check-in",
            f"Event ID: {event_id}",
            f"Date: {event_date.isoformat()}",
            f"Nonce: {nonce}",
        ]
    )

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


@app.get("/api/events/{event_id}", response_model=EventSchema)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

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
            venti_parser.run(limit=5, force_publish=False)
        elif source_name == "catpass":
            catpass_parser.run(limit=5, force_publish=False)
        elif source_name == "passline":
            passline_parser.run(limit=5, force_publish=False)
        elif source_name == "bombo":
            bombo_parser.run(limit=5, force_publish=False)
    except Exception as e:
        logger.error(f"Error running scraper {source_name}: {e}")

@app.post("/api/scrape/{source_name}", response_model=ScrapeResponse)
async def trigger_scrape(
    source_name: str,
    background_tasks: BackgroundTasks,
    _auth: None = Depends(require_scrape_key),
):
    valid_sources = ["venti", "catpass", "passline", "bombo"]
    if source_name not in valid_sources:
        raise HTTPException(status_code=400, detail="Invalid source")
    
    background_tasks.add_task(run_scraper_bg, source_name)
    
    return {"message": f"Scraper {source_name} started in background", "source": source_name}


@app.post("/api/checkin/challenge", response_model=CheckInChallengeResponse)
def checkin_challenge(payload: CheckInChallengeRequest, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    nonce = secrets.token_urlsafe(16)
    message = build_checkin_message(event.id, event.date, nonce)
    return {"event_id": event.id, "nonce": nonce, "message": message}


@app.post("/api/checkin/verify", response_model=CheckInVerifyResponse)
def checkin_verify(payload: CheckInVerifyRequest, db: Session = Depends(get_db)):
    event = db.query(Event).filter_by(id=payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    expected_message = build_checkin_message(event.id, event.date, payload.nonce)
    if payload.message != expected_message:
        raise HTTPException(status_code=400, detail="Invalid check-in message")

    if db.query(CheckIn).filter_by(nonce=payload.nonce).first():
        raise HTTPException(status_code=409, detail="Nonce already used")

    normalized = payload.wallet_address.strip().lower()
    try:
        recovered = Account.recover_message(
            encode_defunct(text=payload.message), signature=payload.signature
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if recovered.lower() != normalized:
        raise HTTPException(status_code=401, detail="Signature does not match wallet")

    existing = (
        db.query(CheckIn)
        .filter_by(event_id=event.id, wallet_address=normalized)
        .first()
    )
    if existing:
        return {
            "status": "already_checked_in",
            "checkin_id": existing.id,
            "created_at": existing.created_at,
        }

    checkin = CheckIn(
        event_id=event.id,
        wallet_address=normalized,
        message=payload.message,
        signature=payload.signature,
        nonce=payload.nonce,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return {
        "status": "checked_in",
        "checkin_id": checkin.id,
        "created_at": checkin.created_at,
    }


@app.get("/api/checkin/status", response_model=CheckInStatusResponse)
def checkin_status(
    event_id: int = Query(...),
    wallet_address: str = Query(...),
    db: Session = Depends(get_db),
):
    normalized = wallet_address.strip().lower()
    checkin = (
        db.query(CheckIn)
        .filter_by(event_id=event_id, wallet_address=normalized)
        .first()
    )
    if not checkin:
        return {"status": "not_checked_in"}
    return {
        "status": "checked_in",
        "checkin_id": checkin.id,
        "created_at": checkin.created_at,
    }

@app.post("/api/openfort/session")
async def create_openfort_session():
    """
    Creates an encryption session for Openfort automatic wallet recovery.
    This bridge is required to keep shield secret keys on the backend.
    """
    if not OPENFORT_SHIELD_SECRET_KEY or not OPENFORT_SHIELD_ENCRYPTION_SHARE:
        logger.error("Openfort Shield keys not configured in .env")
        raise HTTPException(status_code=500, detail="Openfort Shield keys not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://shield.openfort.io/project/encryption-session",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": NEXT_PUBLIC_SHIELD_PUBLISHABLE_KEY or "",
                    "x-api-secret": OPENFORT_SHIELD_SECRET_KEY,
                },
                json={
                    "encryption_part": OPENFORT_SHIELD_ENCRYPTION_SHARE
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Openfort Shield API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to create Openfort session")
                
            data = response.json()
            return {"session": data.get("session")}
    except Exception as e:
        logger.exception("Exception while creating Openfort session")
        raise HTTPException(status_code=500, detail=str(e))
