# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized (tables created if needed).")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
