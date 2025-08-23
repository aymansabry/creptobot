from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trades.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    pair = Column(String, nullable=False)
    profit = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def add_trade(pair: str, profit: float):
    session = Session()
    trade = Trade(pair=pair, profit=profit)
    session.add(trade)
    session.commit()
    session.close()

def get_last_trades(limit=5):
    session = Session()
    trades = session.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
    session.close()
    return trades
