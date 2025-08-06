from sqlalchemy import Column, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)  # Telegram User ID
    username = Column(String)
    balance = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    trading_mode = Column(String, default='virtual')  # virtual/real

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(String, primary_key=True)
    user_id = Column(String)
    amount = Column(Float)
    profit = Column(Float)
    status = Column(String)  # pending/completed/failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
