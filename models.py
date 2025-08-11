# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    role = Column(String(20), default="client")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # علاقة مع جدول AccountKeys
    account_keys = relationship("AccountKeys", back_populates="user")

class AccountKeys(Base):
    __tablename__ = "account_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, nullable=False)
    passphrase = Column(Text, nullable=True)
    exchange = Column(String(50), nullable=False)  # اسم المنصة
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # علاقة مع جدول User
    user = relationship("User", back_populates="account_keys")
