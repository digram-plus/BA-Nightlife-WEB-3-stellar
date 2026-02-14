import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import Config

DB_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if not DB_URL:
    DB_URL = f"postgresql+psycopg2://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
else:
    # Ensure psycopg2 driver is used if it's a raw postgres:// URL
    if DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DB_URL.startswith("postgresql://"):
        DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
