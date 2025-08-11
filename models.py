from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    role = Column(String(20), default='client')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # مفاتيح Binance (مشفرة)
    binance_api_key = Column(String, nullable=True)
    binance_api_secret = Column(String, nullable=True)

    # مفاتيح KuCoin (مشفرة)
    kucoin_api_key = Column(String, nullable=True)
    kucoin_api_secret = Column(String, nullable=True)

    # الرصيد والأرباح
    balance = Column(Float, default=0.0)   # رصيد المستخدم
    profits = Column(Float, default=0.0)   # إجمالي الأرباح

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, balance={self.balance}, profits={self.profits})>"
