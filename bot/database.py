from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    wallet_address = Column(String)
    balance = Column(Float, default=0)
    is_active = Column(Boolean, default=True)

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    trade_type = Column(String)
    buy_currency = Column(String)
    sell_currency = Column(String)
    buy_price = Column(Float)
    sell_price = Column(Float)
    amount = Column(Float)
    profit = Column(Float)
    fee = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    trade_data = Column(JSON)  # بدلاً من metadata

engine = create_engine(Config.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()
