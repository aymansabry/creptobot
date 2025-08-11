# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# جلب رابط قاعدة البيانات من .env
DATABASE_URL = os.getenv("DATABASE_URL")

# لو مش موجود، استخدام SQLite كخيار افتراضي
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./bot.db"

# إنشاء محرك الاتصال
engine = create_engine(DATABASE_URL, echo=True)

# جلسة قاعدة البيانات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# قاعدة النماذج
Base = declarative_base()

def init_db():
    """إنشاء الجداول في قاعدة البيانات"""
    from models import User, AccountKeys  # استيراد الموديلات هنا لتجنب الحلقات
    print(f"Connecting to database: {DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully.")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
