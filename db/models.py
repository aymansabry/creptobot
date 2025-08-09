from sqlalchemy import Table, Column, Integer, BigInteger, Text, Numeric, JSON, TIMESTAMP, Boolean, MetaData, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(Text)
    role = Column(Text, nullable=False, default='user')
    api_exchange = Column(JSON, default={})
    trade_limit = Column(Numeric, default=100)
    mode = Column(Text, default='simulate')
    profit_share_pct = Column(Numeric, default=10)
    owed_profit = Column(Numeric, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    pair = Column(Text)
    buy_exchange = Column(Text)
    buy_price = Column(Numeric)
    sell_exchange = Column(Text)
    sell_price = Column(Numeric)
    amount = Column(Numeric)
    gross_profit = Column(Numeric)
    admin_cut = Column(Numeric)
    net_profit = Column(Numeric)
    status = Column(Text)
    simulated = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
