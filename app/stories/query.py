from datetime import date
from sqlalchemy.orm import Session
from ..models import Event

def pick_today_events(db: Session, top_n: int = 3):
    q = (db.query(Event)
           .filter(Event.date == date.today())
           .filter(Event.status.in_(["queued", "published"]))
           .order_by(Event.time.asc().nulls_last(), Event.title.asc())
           .limit(top_n))
    return list(q)
