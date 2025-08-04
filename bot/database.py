from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language = Column(String(10), default='ar')
    registration_date = Column(DateTime, default=datetime.utcnow)
    wallet_address = Column(String(100))
    balance = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    last_interaction = Column(DateTime)

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    transaction_type = Column(String(20))  # 'deposit', 'withdrawal', 'investment', 'profit'
    amount = Column(Float)
    currency = Column(String(10))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20))  # 'pending', 'completed', 'failed'
    details = Column(JSON)

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    trade_type = Column(String(20))  # 'arbitrage', 'continuous'
    buy_currency = Column(String(10))
    sell_currency = Column(String(10))
    buy_price = Column(Float)
    sell_price = Column(Float)
    amount = Column(Float)
    profit = Column(Float)
    fee = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20))  # 'open', 'completed', 'failed'
    metadata = Column(JSON)  # Additional trade data

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    report_data = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

# Initialize database
def init_db():
    engine = create_engine(Config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

# Database session factory
def get_db_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize database
engine = init_db()
Session = get_session(engine)
