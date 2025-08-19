from sqlalchemy import Column, Integer, String, Float, DateTime, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

# ✅ جدول المستخدمين
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())

# ✅ جدول الصفقات المنفذة
class ArbitrageLog(Base):
    __tablename__ = 'arbitrage_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    amount = Column(Float)
    buy_price = Column(Float)
    sell_price = Column(Float)
    profit = Column(Float)
    executed_at = Column(DateTime, default=func.now())

# ✅ إعداد الاتصال بقاعدة البيانات
DATABASE_URL = "sqlite:///arbitrage.db"  # ← غيّرها لـ MySQL على Railway لو جاهز
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# ✅ دالة تسجيل صفقة جديدة
def log_arbitrage(user_id, symbol, amount, buy_price, sell_price, profit):
    log = ArbitrageLog(
        user_id=user_id,
        symbol=symbol,
        amount=amount,
        buy_price=buy_price,
        sell_price=sell_price,
        profit=profit
    )
    session.add(log)
    session.commit()

# ✅ دالة تحديث رصيد المستخدم
def update_wallet(user_id, profit):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.balance += profit
        session.commit()
    else:
        print(f"❌ المستخدم غير موجود: {user_id}")

# ✅ دالة إنشاء الجداول تلقائيًا
def init_db():
    Base.metadata.create_all(engine)