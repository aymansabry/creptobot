# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import DATABASE_URL, DEFAULT_BOT_FEE_PERCENT

# تهيئة SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# نموذج الإعدادات
class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    k = Column(String(255), unique=True, nullable=False)
    v = Column(Text, nullable=False)

# نموذج المستخدم
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    role = Column(String(20), default="client")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# نموذج حساب المنصة
class ExchangeAccount(Base):
    __tablename__ = "exchange_accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    exchange_name = Column(String(50), nullable=False)
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    status = Column(String(10), default="inactive")  # active / inactive
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# إنشاء الجداول
def init_db():
    Base.metadata.create_all(bind=engine)
    # إدخال قيمة افتراضية للـ bot_fee_percent إذا غير موجودة
    db = SessionLocal()
    if not db.query(Setting).filter_by(k="bot_fee_percent").first():
        setting = Setting(k="bot_fee_percent", v=str(DEFAULT_BOT_FEE_PERCENT))
        db.add(setting)
        db.commit()
    db.close()

# قراءة إعداد
def get_setting(key, default=None):
    db = SessionLocal()
    setting = db.query(Setting).filter_by(k=key).first()
    db.close()
    return setting.v if setting else default

# تعديل/إضافة إعداد
def set_setting(key, value):
    db = SessionLocal()
    setting = db.query(Setting).filter_by(k=key).first()
    if setting:
        setting.v = str(value)
    else:
        setting = Setting(k=key, v=str(value))
        db.add(setting)
    db.commit()
    db.close()
