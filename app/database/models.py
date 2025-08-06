from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String)
    wallet_address = Column(String)  # محفظة العميل الأصلية
    virtual_wallet_address = Column(String)  # المحفظة الوهمية المخصصة له
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Investment(Base):
    __tablename__ = 'investments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    status = Column(String, default="pending")  # pending, active, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    profit = Column(Float, default=0.0)

class TransactionLog(Base):
    __tablename__ = 'transaction_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    tx_type = Column(String)  # deposit, profit, fee
    amount = Column(Float)
    tx_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
