from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    wallet_address = Column(String)
    is_admin = Column(Boolean, default=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    tx_type = Column(String)
    amount = Column(Float)
    tx_hash = Column(String)

