# models.py
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # مفاتيح مشفرة لكل مستخدم
    binance_api_key = Column(Text, nullable=True)
    binance_api_secret = Column(Text, nullable=True)
    kucoin_api_key = Column(Text, nullable=True)
    kucoin_api_secret = Column(Text, nullable=True)
    kucoin_api_passphrase = Column(Text, nullable=True)

    # معلومات الاستثمار
    investment_amount = Column(Float, default=0.0)      # المبلغ المبدئي
    total_profit_loss = Column(Float, default=0.0)      # إجمالي الربح/الخسارة
    last_snapshot_balance = Column(Float, default=0.0)  # لقيمة العرض السريع
    mode = Column(String(20), default="demo")           # demo أو live
