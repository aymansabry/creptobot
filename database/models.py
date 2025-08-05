from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    first_name = Column(String(50))
    last_name = Column(String(50))
    registration_date = Column(DateTime, default=datetime.utcnow)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    wallets = relationship("Wallet", back_populates="user")
    trades = relationship("Trade", back_populates="user")

class Wallet(Base):
    __tablename__ = 'wallets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    currency = Column(String(10), default='USDT')
    balance = Column(Float, default=0.0)
    address = Column(String(100))
    
    user = relationship("User", back_populates="wallets")

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USDT')
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    profit = Column(Float)
    status = Column(String(20), default='pending')  # pending, active, completed, cancelled
    risk_level = Column(Float)
    
    user = relationship("User", back_populates="trades")
    steps = relationship("TradeStep", back_populates="trade")

class TradeStep(Base):
    __tablename__ = 'trade_steps'
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trades.id'))
    step_type = Column(String(50))  # buy, sell, transfer
    exchange = Column(String(50))
    currency_pair = Column(String(20))
    amount = Column(Float)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    trade = relationship("Trade", back_populates="steps")
