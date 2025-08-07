from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    pair = Column(String)
    amount = Column(Float)
    profit = Column(Float)
    timestamp = Column(DateTime)
