from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)