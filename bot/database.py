from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

# تأكد من اتصال PostgreSQL على Railway
def init_db():
    db_url = Config.DATABASE_URL
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(db_url)
    
    # أنشئ الجداول إذا لم تكن موجودة
    Base.metadata.create_all(engine)
    
    return engine

# إنشاء جلسة عمل
def get_db_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()
