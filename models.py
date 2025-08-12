#models.py
from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(50))
    first_name = Column(String(50))
    role = Column(String(20), default="client")
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
