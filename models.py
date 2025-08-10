from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    role = Column(String(20), default='client')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    api_keys = relationship('APIKey', back_populates='user')
    daily_loss_limit = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)   # هل الاستثمار مفعّل
    investment_amount = Column(Float, default=0.0)  # مبلغ الاستثمار المسموح به

class APIKey(Base):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    exchange = Column(String(50))
    api_key_encrypted = Column(Text)
    api_secret_encrypted = Column(Text)
    passphrase_encrypted = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship('User', back_populates='api_keys')

class TradeLog(Base):
    __tablename__ = 'trade_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    exchange = Column(String(50))
    side = Column(String(10))  # buy أو sell
    symbol = Column(String(50))
    qty = Column(Float)
    price = Column(Float)
    profit = Column(Float, nullable=True)
    raw = Column(Text)
    status = Column(String(20), default='OK')
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)