from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    role = Column(String, default="user")

class Investment(Base):
    __tablename__ = 'investments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # "pending", "completed"
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

class Profit(Base):
    __tablename__ = 'profits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)

class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    event = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    user_id = Column(Integer, nullable=True)
