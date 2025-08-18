from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExchangeAccount(Base):
    __tablename__ = 'exchange_accounts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    exchange = Column(String)
    api_key = Column(String)
    api_secret = Column(String)
    is_valid = Column(Boolean, default=False)