from app.db import SessionLocal
from app.models import Event

DEFAULT_WALLET = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

def fix_wallets():
    db = SessionLocal()
    try:
        # Update all events that are published but lack a wallet
        events = db.query(Event).filter(
            Event.status == "published",
            (Event.support_wallet == None) | (Event.support_wallet == "")
        ).all()
        
        print(f"Found {len(events)} events without a support wallet.")
        
        for ev in events:
            ev.support_wallet = DEFAULT_WALLET
            
        db.commit()
        print("Successfully updated all published events with default wallet.")
    finally:
        db.close()

if __name__ == "__main__":
    fix_wallets()
