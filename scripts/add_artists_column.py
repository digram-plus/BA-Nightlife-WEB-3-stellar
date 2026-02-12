import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    user = os.getenv("POSTGRES_USER")
    pw = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    
    db_url = f"postgresql://{user}:{pw}@{host}:{port}/{db_name}"
    
    print(f"Connecting to {host}:{port}/{db_name}...")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Adding 'artists' column to 'events' table...")
        # Postgres check for column existence
        check_query = text("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name='events' AND column_name='artists'
        """)
        result = conn.execute(check_query).scalar()
        
        if result == 0:
            conn.execute(text("ALTER TABLE events ADD COLUMN artists VARCHAR[]"))
            conn.commit()
            print("Column 'artists' added successfully.")
        else:
            print("Column 'artists' already exists.")

if __name__ == "__main__":
    main()
