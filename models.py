from sqlalchemy import Column, Integer, String, Float, Text, DateTime
import datetime
from database import Base  # استيراد الـ Base الموحد من database.py

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    role = Column(String(20), default='client')

    # مفاتيح API للمنصات المختلفة
    binance_api_key = Column(Text, nullable=True)
    binance_api_secret = Column(Text, nullable=True)

    kucoin_api_key = Column(Text, nullable=True)
    kucoin_api_secret = Column(Text, nullable=True)
    kucoin_api_passphrase = Column(Text, nullable=True)

    # بيانات الاستثمار والمراجحة
    investment_amount = Column(Float, default=0.0)
    mode = Column(String(10), default='demo')  # live أو demo

    total_profit_loss = Column(Float, default=0.0)
    last_snapshot_balance = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
