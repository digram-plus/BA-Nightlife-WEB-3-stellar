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
        print("Listing last 20 events...")
        query = text("SELECT title, venue, city, status FROM events ORDER BY created_at DESC LIMIT 20")
        res = conn.execute(query)
        rows = res.fetchall()
        for row in rows:
            print(f"Title: {row[0]} | Venue: {row[1]} | City: {row[2]} | Status: {row[3]}")

if __name__ == "__main__":
    main()
