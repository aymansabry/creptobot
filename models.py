from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    role = Column(String(20), default='client')

    # مفاتيح API في جدول المستخدم غير ضروري لو تستخدم جدول AccountKeys فقط
    # لكن هنا مخزنين المفاتيح في الجدول User مباشرة
    binance_api_key = Column(Text, nullable=True)
    binance_api_secret = Column(Text, nullable=True)

    kucoin_api_key = Column(Text, nullable=True)
    kucoin_api_secret = Column(Text, nullable=True)
    kucoin_api_passphrase = Column(Text, nullable=True)

    # بيانات الاستثمار والمراجحة
    investment_amount = Column(Float, default=0.0)
    mode = Column(String(10), default='demo')  # 'live' أو 'demo'

    total_profit_loss = Column(Float, default=0.0)
    last_snapshot_balance = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # علاقة واحد إلى متعدد مع مفاتيح الحساب (اختياري لو تستخدم جدول AccountKeys)
    account_keys = relationship("AccountKeys", back_populates="user")

class AccountKeys(Base):
    __tablename__ = 'account_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, nullable=False)
    passphrase = Column(Text, nullable=True)
    exchange = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="account_keys")
