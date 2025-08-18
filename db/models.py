from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    telegram_id = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    daily_profit = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    created_at = Column(String)

class ExchangeAPI(Base):
    __tablename__ = 'exchange_apis'
    
    user_id = Column(String, primary_key=True)
    exchange = Column(String, primary_key=True)
    api_key = Column(String)
    api_secret = Column(String)
    is_valid = Column(Boolean, default=False)

class SubWallet(Base):
    __tablename__ = 'sub_wallets'
    
    user_id = Column(String, primary_key=True)
    exchange = Column(String, primary_key=True)
    sub_account = Column(String, primary_key=True)
    currency = Column(String)
    balance = Column(Float)
    max_allowed = Column(Float)
    is_active = Column(Boolean, default=True)

class TradeHistory(Base):
    __tablename__ = 'trade_history'
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    exchange_from = Column(String)
    exchange_to = Column(String)
    currency_pair = Column(String)
    amount = Column(Float)
    profit = Column(Float)
    commission = Column(Float)
    timestamp = Column(String)
    status = Column(String)  # completed, failed, refunded