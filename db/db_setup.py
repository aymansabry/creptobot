import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Float, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    investment_amount = Column(Float, default=0)
    min_profit_percent = Column(Float, default=0)
    trading_active = Column(Boolean, default=False)
    auto_transfer_allowed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExchangeCredential(Base):
    __tablename__ = "exchange_credentials"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    exchange_id = Column(String(50))
    api_key = Column(String(256))
    secret = Column(String(256))
    passphrase = Column(String(256), nullable=True)
    active = Column(Boolean, default=True)
    last_verified = Column(DateTime, nullable=True)

class ArbitrageHistory(Base):
    __tablename__ = "arbitrage_history"
    id = Column(Integer, primary_key=True)
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

def init_db():
    logger.info("إنشاء أو تحديث الجداول إذا لم تكن موجودة...")
    Base.metadata.create_all(engine)
    logger.info("جاهز للعمل.")