from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Enum, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func, text
from config import Config
import enum
import logging

# إعداد التسجيل
logger = logging.getLogger(__name__)

Base = declarative_base()

class ExchangePlatform(enum.Enum):
    BINANCE = "binance"
    KUCOIN = "kucoin"
    BYBIT = "bybit"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    mode = Column(Enum('live', 'demo', name='user_mode'), default='demo')
    investment_amount = Column(Float(precision=2), default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

class ExchangeConnection(Base):
    __tablename__ = 'exchange_connections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    platform = Column(Enum(ExchangePlatform), nullable=False)
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, nullable=False)
    passphrase = Column(Text)  # لبعض المنصات مثل KuCoin
    is_valid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ExchangeConnection(user_id={self.user_id}, platform={self.platform})>"

class Database:
    def __init__(self):
        try:
            self.engine = create_engine(
                Config.DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'connect_timeout': 10
                }
            )
            
            # إصلاح مشكلة MySQL مع TIMESTAMP
            with self.engine.connect() as conn:
                conn.execute(text("SET SESSION sql_mode='ALLOW_INVALID_DATES';"))
                conn.commit()

            self.Session = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
            logger.info("تم الاتصال بقاعدة البيانات بنجاح وإنشاء الجداول")
            
        except Exception as e:
            logger.error(f"فشل في الاتصال بقاعدة البيانات: {str(e)}")
            raise

    def get_user(self, telegram_id: int) -> Optional[User]:
        session = self.Session()
        try:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدم: {str(e)}")
            return None
        finally:
            session.close()

    def add_user(self, user_data: dict) -> Optional[User]:
        session = self.Session()
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إضافة مستخدم: {str(e)}")
            return None
        finally:
            session.close()

    def update_user(self, telegram_id: int, update_data: dict) -> bool:
        session = self.Session()
        try:
            rows_updated = session.query(User).filter_by(telegram_id=telegram_id).update(update_data)
            session.commit()
            return rows_updated > 0
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تحديث المستخدم: {str(e)}")
            return False
        finally:
            session.close()

    def add_exchange_connection(self, connection_data: dict) -> Optional[ExchangeConnection]:
        session = self.Session()
        try:
            connection = ExchangeConnection(**connection_data)
            session.add(connection)
            session.commit()
            return connection
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إضافة اتصال منصة: {str(e)}")
            return None
        finally:
            session.close()

    def get_active_connections(self, user_id: int) -> List[ExchangeConnection]:
        session = self.Session()
        try:
            return session.query(ExchangeConnection).filter_by(
                user_id=user_id,
                is_active=True
            ).all()
        except Exception as e:
            logger.error(f"خطأ في جلب اتصالات المنصات: {str(e)}")
            return []
        finally:
            session.close()

    def update_connection_status(self, connection_id: int, is_active: bool) -> bool:
        session = self.Session()
        try:
            rows_updated = session.query(ExchangeConnection).filter_by(
                id=connection_id
            ).update({'is_active': is_active})
            session.commit()
            return rows_updated > 0
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تحديث حالة الاتصال: {str(e)}")
            return False
        finally:
            session.close()
