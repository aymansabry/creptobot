from sqlalchemy import Column, Integer, String, Float, DateTime, Text, BigInteger
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # بيانات API لكل مستخدم (مشفرة لاحقاً)
    binance_api_key = Column(Text)
    binance_secret_key = Column(Text)
    kucoin_api_key = Column(Text)
    kucoin_secret_key = Column(Text)
    kucoin_passphrase = Column(Text)

    # الاستثمار
    balance = Column(Float, default=0.0)   # الرصيد الحالي
    profits = Column(Float, default=0.0)   # الأرباح التراكمية

    # وضع التداول (حي / تجريبي)
    mode = Column(String(20), default="live")
