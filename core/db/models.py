from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from core.config import OperationMode

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    accepted_terms = Column(Boolean, default=False)

class UserWallet(Base):
    __tablename__ = 'user_wallets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    wallet_type = Column(Enum(OperationMode), default=OperationMode.SIMULATION)
    address = Column(String(100))
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)

class SystemSettings(Base):
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True)
    allow_simulation = Column(Boolean, default=True)
    real_trading_enabled = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
