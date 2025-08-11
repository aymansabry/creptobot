# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# قراءة بيانات الاتصال من المتغيرات البيئية
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "mydb")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# إنشاء المحرك
engine = create_engine(DATABASE_URL, echo=False)

# إعداد الـ Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base لإنشاء الجداول
Base = declarative_base()

# استدعاء النماذج بعد Base لتسجيلها
from models import User  # تأكد أن لديك ملف models.py يحتوي على الكلاسات

def init_db():
    """إنشاء الجداول إذا لم تكن موجودة"""
    Base.metadata.create_all(bind=engine)
