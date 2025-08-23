# db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# قراءة عنوان قاعدة البيانات من متغيرات البيئة.
# إذا لم يكن موجودًا، سيتم استخدام قاعدة بيانات SQLite محلية.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_bot.db")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    api_key = Column(String)
    api_secret = Column(String)
    trading_amount = Column(Float, default=5.0)

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    pair = Column(String)
    profit = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# إنشاء الجداول في قاعدة البيانات
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ====================
# Functions for CRUD operations
# ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_user(telegram_id: int):
    """إنشاء مستخدم جديد إذا لم يكن موجودًا بالفعل."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            new_user = User(telegram_id=telegram_id)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"User with telegram_id {telegram_id} created.")
            return new_user
        return user
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

async def save_api_keys(telegram_id: int, api_key: str, api_secret: str):
    """حفظ مفاتيح API للمستخدم."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.api_key = api_key
            user.api_secret = api_secret
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_user_api_keys(telegram_id: int):
    """استرجاع مفاتيح API للمستخدم."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            return user.api_key, user.api_secret
        return None, None
    finally:
        db.close()

async def save_amount(telegram_id: int, amount: float):
    """حفظ مبلغ التداول للمستخدم."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.trading_amount = amount
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_amount(telegram_id: int):
    """استرجاع مبلغ التداول للمستخدم."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            return user.trading_amount
        return None
    finally:
        db.close()

def add_trade(telegram_id: int, pair: str, profit: float):
    """إضافة صفقة جديدة إلى قاعدة البيانات."""
    db = SessionLocal()
    try:
        new_trade = Trade(user_id=telegram_id, pair=pair, profit=profit)
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)
        return new_trade
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

def get_last_trades(telegram_id: int):
    """استرجاع آخر الصفقات للمستخدم."""
    db = SessionLocal()
    try:
        trades = db.query(Trade).filter(Trade.user_id == telegram_id).order_by(Trade.timestamp.desc()).all()
        return trades
    finally:
        db.close()
