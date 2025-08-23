from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from datetime import datetime
from config import settings

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    exchange: Mapped[str] = mapped_column(String(32), default="binance")
    api_key: Mapped[str] = mapped_column(Text)
    api_secret: Mapped[str] = mapped_column(Text)
    can_withdraw: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class AccountSetting(Base):
    __tablename__ = "account_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    trading_amount_usdt: Mapped[float] = mapped_column(Float, default=10.0)
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    bnb_reserve: Mapped[float] = mapped_column(Float, default=settings.bnb_min_reserve)
    accumulated_profit: Mapped[float] = mapped_column(Float, default=0.0)
    last_compound_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    length: Mapped[int] = mapped_column(Integer)
    route: Mapped[str] = mapped_column(String(512))
    expected_gross_pct: Mapped[float] = mapped_column(Float)
    expected_net_pct: Mapped[float] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(String(255))
    viable: Mapped[bool] = mapped_column(Boolean, default=False)

class Trade(Base):
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    route: Mapped[str] = mapped_column(String(512))
    length: Mapped[int] = mapped_column(Integer)
    notional_usdt: Mapped[float] = mapped_column(Float)
    gross_pct: Mapped[float | None] = mapped_column(Float)
    net_pct: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="running")
    details: Mapped[dict | None] = mapped_column(JSON)

class FeeLedger(Base):
    __tablename__ = "fee_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profit_usdt: Mapped[float] = mapped_column(Float)
    fee_pct: Mapped[float] = mapped_column(Float)
    fee_usdt: Mapped[float] = mapped_column(Float)
    settled: Mapped[bool] = mapped_column(Boolean, default=False)
    tx_ref: Mapped[str | None] = mapped_column(String(128))
