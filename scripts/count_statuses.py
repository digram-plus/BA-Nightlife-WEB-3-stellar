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
        print("Fetching event counts by status...")
        query = text("SELECT status, count(*) FROM events GROUP BY status")
        res = conn.execute(query)
        rows = res.fetchall()
        if not rows:
            print("No events found in table.")
        for row in rows:
            print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    main()
