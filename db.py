import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# ------------ Models ------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, index=True)
    api_key = Column(String(255), nullable=True)
    api_secret = Column(String(255), nullable=True)
    amount = Column(Float, default=0.0)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50))
    pair = Column(String(20))
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ------------ Functions ------------
def init_db():
    Base.metadata.create_all(bind=engine)

def create_user(telegram_id: str):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        session.commit()
    session.close()
    return user

def save_api_keys(telegram_id: str, api_key: str, api_secret: str):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.api_key = api_key
        user.api_secret = api_secret
        session.commit()
    session.close()

def get_user_api_keys(telegram_id: str):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    if user:
        return user.api_key, user.api_secret
    return None, None

def save_amount(telegram_id: str, amount: float):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.amount = amount
        session.commit()
    session.close()

def get_amount(telegram_id: str):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    if user:
        return user.amount
    return 0.0

def get_last_trades(telegram_id: str, limit: int = 5):
    session = SessionLocal()
    trades = (
        session.query(Trade)
        .filter_by(telegram_id=telegram_id)
        .order_by(Trade.timestamp.desc())
        .limit(limit)
        .all()
    )
    session.close()
    return trades
