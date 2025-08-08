# project_root/db/models.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True) # تم التعديل
    username = Column(String)
    wallets = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    
class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), unique=True) # تم التعديل
    balance_usdt = Column(Float, default=0.0)
    is_continuous_trading = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="wallets")
    
class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    user_id = Column(BigInteger, ForeignKey("users.user_id")) # تم التعديل
    symbol = Column(String)
    exchange = Column(String)
    type = Column(String) # 'spot', 'futures', 'arbitrage'
    status = Column(String, default="open") # 'open', 'closed'
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    amount = Column(Float)
    profit = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="trades")
    
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id")) # تم التعديل
    type = Column(String) # 'deposit', 'withdrawal', 'profit'
    amount = Column(Float)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="transactions")
