from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    is_admin = Column(Boolean, default=False)
    continuous_mode = Column(Boolean, default=False)
    wallet = relationship("Wallet", back_populates="owner", uselist=False)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    address = Column(String)
    balance = Column(Float, default=0.0)
    owner = relationship("User", back_populates="wallet")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Deposit(Base):
    __tablename__ = "deposits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Float)
    confirmed = Column(Boolean, default=False)
