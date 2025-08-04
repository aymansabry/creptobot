from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)  # تأكد من عدم وجود تكرار
    first_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# الاتصال الآمن بقاعدة البيانات
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db():
    return Session()
