from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    wallet_address = Column(String)  # Original wallet for payout
    registered_at = Column(DateTime, default=func.now())

    investments = relationship("Investment", back_populates="user")

class Investment(Base):
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    profit = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, running, completed
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="investments")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    tx_hash = Column(String, unique=True)
    amount = Column(Float)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
