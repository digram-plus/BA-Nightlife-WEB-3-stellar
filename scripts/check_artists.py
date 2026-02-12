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
        print("Checking Black Cream events...")
        query = text("SELECT title, artists FROM events WHERE title ILIKE '%BLACK CREAM%' LIMIT 5")
        res = conn.execute(query)
        rows = res.fetchall()
        if not rows:
            print("No events found.")
        for row in rows:
            print(f"Title: {row[0]}")
            print(f"Artists: {row[1]}")
            print("-" * 20)

if __name__ == "__main__":
    main()
