from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, Boolean, Enum, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func, text
from config import Config
import enum
import logging
from typing import Optional, List, Dict, Any
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import ccxt
import hashlib

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# إنشاء أداة التشفير
try:
    cipher = Fernet(Config.ENCRYPTION_KEY.encode())
except Exception as e:
    logger.error(f"خطأ في تهيئة التشفير: {e}")
    raise

class ExchangePlatform(enum.Enum):
    BINANCE = "binance"
    KUCOIN = "kucoin"
    BYBIT = "bybit"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)  # تغيير من Integer إلى BigInteger
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    mode = Column(Enum('live', 'demo', name='user_mode'), default='demo')
    investment_amount = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    demo_balance = Column(Float, default=10000.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

class ExchangeConnection(Base):
    __tablename__ = 'exchange_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)  # تغيير من Integer إلى BigInteger
    platform = Column(Enum(ExchangePlatform), nullable=False)
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, nullable=False)
    passphrase = Column(Text)
    is_valid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ExchangeConnection(user_id={self.user_id}, platform={self.platform})>"

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)  # تغيير من Integer إلى BigInteger
    platform = Column(String(50))
    symbol = Column(String(20))
    amount = Column(Float, nullable=False)
    profit = Column(Float)
    type = Column(Enum('live', 'demo', name='transaction_type'))
    status = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Transaction(user_id={self.user_id}, amount={self.amount})>"

class ArbitrageOpportunity(Base):
    __tablename__ = 'arbitrage_opportunities'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    buy_exchange = Column(String(50), nullable=False)
    sell_exchange = Column(String(50), nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    profit_percentage = Column(Float, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<ArbitrageOpportunity(symbol={self.symbol}, profit={self.profit_percentage}%)>"

class Database:
    def __init__(self):
        try:
            # تعديل رابط الاتصال ليكون متوافقًا مع SQLAlchemy
            db_url = Config.DATABASE_URL
            if db_url.startswith("mysql://"):
                db_url = db_url.replace("mysql://", "mysql+pymysql://")
            
            self.engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'connect_timeout': 10,
                    'ssl': {'ssl_mode': 'preferred'}
                }
            )
            
            # إصلاح مشاكل MySQL
            with self.engine.begin() as conn:
                conn.execute(text("SET SESSION sql_mode='ALLOW_INVALID_DATES';"))
                conn.execute(text("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            
            self.Session = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة قاعدة البيانات: {e}")
            raise

    # ---- وظائف التشفير ----
    def encrypt(self, data: str) -> str:
        """تشفير البيانات الحساسة"""
        try:
            return cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"خطأ في التشفير: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """فك تشفير البيانات"""
        try:
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"خطأ في فك التشفير: {e}")
            raise

    # ---- إدارة المستخدمين ----
    def get_user(self, telegram_id: int) -> Optional[User]:
        """الحصول على بيانات مستخدم"""
        session = self.Session()
        try:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدم: {e}")
            return None
        finally:
            session.close()

    def add_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """إضافة مستخدم جديد"""
        session = self.Session()
        try:
            # التحقق من وجود المستخدم أولاً
            existing_user = self.get_user(user_data['telegram_id'])
            if existing_user:
                logger.warning(f"المستخدم {user_data['telegram_id']} موجود بالفعل")
                return existing_user
                
            # تعيين القيم الافتراضية
            user_data.setdefault('mode', 'demo')
            user_data.setdefault('investment_amount', 0.0)
            user_data.setdefault('balance', 0.0)
            user_data.setdefault('demo_balance', 10000.0)
            user_data.setdefault('is_active', True)
            
            user = User(**user_data)
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إضافة مستخدم: {e}")
            return None
        finally:
            session.close()

    # ... (بقية الدوال تبقى كما هي مع التأكد من استخدام BigInteger لجميع حقول user_id)

    def update_user(self, telegram_id: int, update_data: Dict[str, Any]) -> bool:
        """تحديث بيانات المستخدم"""
        session = self.Session()
        try:
            rows_updated = session.query(User).filter_by(telegram_id=telegram_id).update(update_data)
            session.commit()
            return rows_updated > 0
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تحديث المستخدم: {e}")
            return False
        finally:
            session.close()

    # ... (بقية دوال الفئات الأخرى)

    def test_connection(self) -> bool:
        """اختبار اتصال قاعدة البيانات"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ اتصال قاعدة البيانات يعمل بشكل صحيح")
            return True
        except Exception as e:
            logger.error(f"❌ فشل في الاتصال بقاعدة البيانات: {e}")
            return False