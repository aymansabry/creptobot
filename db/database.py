from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import logging

logger = logging.getLogger(__name__)

# إعداد محرك قاعدة البيانات
SQLALCHEMY_DATABASE_URL = Config.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """توفير جلسة قاعدة البيانات للاعتماديات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise