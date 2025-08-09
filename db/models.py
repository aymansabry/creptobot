from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    wallet_balance = Column(Float, default=0.0)
    investment_amount = Column(Float, default=0.0)
    profit_earned = Column(Float, default=0.0)
    trading_mode = Column(String, default="demo")
    active = Column(Boolean, default=True)
    encrypted_binance_api_key = Column(String, nullable=True)
    encrypted_binance_api_secret = Column(String, nullable=True)
    encrypted_kucoin_api_key = Column(String, nullable=True)
    encrypted_kucoin_api_secret = Column(String, nullable=True)
    encrypted_kucoin_api_passphrase = Column(String, nullable=True)
    commission_rate = Column(Float, default=0.01)
    commission_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallets = relationship("Wallet", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="wallets")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    trade_type = Column(String)
    amount = Column(Float)
    profit = Column(Float)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="trades")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
