from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

Base = declarative_base()

class TradeLog(Base):
    __tablename__ = 'trade_logs'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    buy_exchange = Column(String)
    sell_exchange = Column(String)
    buy_price = Column(Float)
    sell_price = Column(Float)
    quantity = Column(Float)
    profit = Column(Float)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())