from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# رابط قاعدة البيانات من المتغيرات البيئية
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# إنشاء المحرك (Engine)
engine = create_engine(DATABASE_URL, echo=False)

# جلسة للتعامل مع القاعدة
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    ينشئ الجداول إذا لم تكن موجودة
    """
    Base.metadata.create_all(bind=engine)

# استدعاء عند تشغيل البوت لأول مرة
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
