#database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL is not set in .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# الجداول
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100), nullable=True)
    role = Column(String(20), default="client")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExchangeAPIKey(Base):
    __tablename__ = "exchange_api_keys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    exchange_name = Column(String(50))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Investment(Base):
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float)
    is_real = Column(Boolean, default=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class TradeRecord(Base):
    __tablename__ = "trade_records"
    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, index=True)
    symbol = Column(String(20))
    side = Column(String(4))
    price = Column(Float)
    amount = Column(Float)
    fee = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True)
    value = Column(String(255))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_setting(db, key: str, default=None):
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            return setting.value
        return default
    except SQLAlchemyError:
        return default

def set_setting(db, key: str, value: str):
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        return False
