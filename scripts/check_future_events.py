import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    load_dotenv()
    user = os.getenv("POSTGRES_USER")
    pw = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")
    
    db_url = f"postgresql://{user}:{pw}@{host}:{port}/{db}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Checking events more than 14 days ahead...")
        query = text("SELECT title, date, status FROM events WHERE date > CURRENT_DATE + INTERVAL '14 days' ORDER BY date ASC LIMIT 20")
        res = conn.execute(query)
        rows = res.fetchall()
        if not rows:
            print("No events found more than 14 days ahead.")
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")
        
        print("\nChecking all queued events regardless of date...")
        query_all_queued = text("SELECT title, date, status FROM events WHERE status = 'queued' ORDER BY date ASC")
        res_all = conn.execute(query_all_queued)
        rows_all = res_all.fetchall()
        print(f"Total queued: {len(rows_all)}")
        for row in rows_all:
             print(f"{row[0]} | {row[1]} | {row[2]}")

if __name__ == "__main__":
    main()
