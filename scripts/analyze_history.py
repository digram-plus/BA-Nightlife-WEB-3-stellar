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
        print("Analyzing last 20 published events...")
        query = text("SELECT title, date, created_at, source_name FROM events WHERE status = 'published' ORDER BY created_at DESC LIMIT 20")
        res = conn.execute(query)
        rows = res.fetchall()
        for row in rows:
            print(f"Title: {row[0]} | Event Date: {row[1]} | Scraped At: {row[2]} | Source: {row[3]}")
        
        print("\nDistribution by Event Date (Next 30 days):")
        query_dist = text("SELECT date, count(*) FROM events WHERE date >= CURRENT_DATE AND date <= CURRENT_DATE + INTERVAL '30 days' GROUP BY date ORDER BY date")
        res_dist = conn.execute(query_dist)
        rows_dist = res_dist.fetchall()
        for row in rows_dist:
            print(f"{row[0]}: {row[1]} events")

if __name__ == "__main__":
    main()
