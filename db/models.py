# project_root/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, unique=True, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    wallet = relationship("Wallet", back_populates="user", uselist=False)

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance_usdt = Column(Float, default=0.0)
    is_continuous_trading = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="wallet")
    trades = relationship("Trade", back_populates="wallet")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    symbol = Column(String)
    exchange = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    amount = Column(Float)
    profit = Column(Float, default=0.0)
    status = Column(String, default="open")
    is_demo = Column(Boolean, default=False)
    type = Column(String)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    wallet = relationship("Wallet", back_populates="trades")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    type = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
