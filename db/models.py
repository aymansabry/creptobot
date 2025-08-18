from sqlalchemy import Column, BigInteger, String, Float, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """نموذج جدول المستخدمين"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    api_key = Column(String, nullable=False)
    api_secret = Column(String, nullable=False)
    trade_percent = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, is_active={self.is_active})>"