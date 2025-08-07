from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Dict, Any

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    first_name = Column(String(50))
    last_name = Column(String(50))
    join_date = Column(DateTime, server_default=func.now())
    is_admin = Column(Integer, default=0)
    status = Column(String(20), default='active')

class Wallet(Base):
    __tablename__ = 'wallets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    address = Column(String(64), unique=True, nullable=False)
    balances = Column(JSON, default={'USDT': 0.0})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    trade_uuid = Column(String(36), unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    buy_exchange = Column(String(20), nullable=False)
    sell_exchange = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    error = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    executed_at = Column(DateTime)

class ContinuousInvestment(Base):
    __tablename__ = 'continuous_investments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    min_profit_percentage = Column(Float, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SystemSettings(Base):
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    min_trade_amount = Column(Float, default=1.0)
    bot_commission = Column(Float, default=0.1)
    risk_threshold = Column(Float, default=0.3)
    updated_by = Column(Integer, ForeignKey('users.id'))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
