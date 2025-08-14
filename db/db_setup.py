import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, BigInteger, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    investment_amount = Column(Float, default=0)
    min_profit_percent = Column(Float, default=0)
    trading_active = Column(Boolean, default=False)
    auto_transfer_allowed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExchangeCredential(Base):
    __tablename__ = "exchange_credentials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    exchange_id = Column(String(50))
    api_key = Column(String(256))
    secret = Column(String(256))
    passphrase = Column(String(256), nullable=True)
    active = Column(Boolean, default=True)
    last_verified = Column(DateTime, nullable=True)

class ArbitrageHistory(Base):
    __tablename__ = "arbitrage_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    symbol = Column(String(50))
    buy_exchange = Column(String(50))
    sell_exchange = Column(String(50))
    buy_price = Column(Float)
    sell_price = Column(Float)
    amount_base = Column(Float)
    amount_quote = Column(Float)
    gross_spread_percent = Column(Float)
    est_fees_percent = Column(Float)
    bot_fee_percent = Column(Float)
    net_profit_quote = Column(Float)
    success = Column(Boolean, default=False)
    error = Column(Text, nullable=True)

Base.metadata.create_all(engine)