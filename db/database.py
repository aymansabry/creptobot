from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core.config import DATABASE_URL
from typing import Generator

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_session() -> Generator[Session, None, None]:
    """Dependency injection style session management."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_session_sync() -> Session:
    return SessionLocal()
