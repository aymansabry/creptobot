from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    balance = Column(Integer, default=0)  # رصيد USD

# الاتصال بقاعدة البيانات
engine = create_engine(Config.DATABASE_URL)
Base.metadata.create_all(engine)  # إنشاء الجداول إذا غير موجودة
Session = sessionmaker(bind=engine)

def get_db():
    return Session()
