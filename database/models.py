from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    balance = Column(Float, default=0.0)
    binance_api_key = Column(String)
    binance_api_secret = Column(String)
    created_at = Column(DateTime)

class Platform(Base):
    __tablename__ = 'platforms'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    api_url = Column(String)
    active = Column(Boolean, default=True)

class ArbitrageLog(Base):
    __tablename__ = 'arbitrage_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String)
    amount = Column(Float)
    buy_price = Column(Float)
    sell_price = Column(Float)
    profit = Column(Float)
    executed_at = Column(DateTime)
