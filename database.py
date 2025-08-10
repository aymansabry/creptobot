import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment variables")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def create_tables():
    print("جاري إنشاء الجداول في قاعدة البيانات...")
    Base.metadata.create_all(bind=engine)
    print("تم إنشاء الجداول بنجاح.")