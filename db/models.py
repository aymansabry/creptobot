from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

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
    trading_mode = Column(String, default="demo")  # demo or real
    active = Column(Boolean, default=True)
