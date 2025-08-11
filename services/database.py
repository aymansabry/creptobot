from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Enum, Text, TIMESTAMP
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

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
cipher = Fernet(Config.ENCRYPTION_KEY.encode())

class ExchangePlatform(enum.Enum):
    BINANCE = "binance"
    KUCOIN = "kucoin"
    BYBIT = "bybit"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
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

class ExchangeConnection(Base):
    __tablename__ = 'exchange_connections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    platform = Column(Enum(ExchangePlatform))
    api_key = Column(Text)
    api_secret = Column(Text)
    passphrase = Column(Text)
    is_valid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    platform = Column(String(50))
    symbol = Column(String(20))
    amount = Column(Float)
    profit = Column(Float)
    type = Column(Enum('live', 'demo', name='transaction_type'))
    status = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())

class ArbitrageOpportunity(Base):
    __tablename__ = 'arbitrage_opportunities'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20))
    buy_exchange = Column(String(50))
    sell_exchange = Column(String(50))
    buy_price = Column(Float)
    sell_price = Column(Float)
    profit_percentage = Column(Float)
    timestamp = Column(TIMESTAMP, server_default=func.now())

class Database:
    def __init__(self):
        self.engine = create_engine(
            Config.DATABASE_URL.replace("mysql://", "mysql+pymysql://"),
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # إصلاح مشاكل MySQL
        with self.engine.connect() as conn:
            conn.execute(text("SET SESSION sql_mode='ALLOW_INVALID_DATES';"))
        
        Base.metadata.create_all(self.engine)
        logger.info("تم تهيئة قاعدة البيانات بنجاح")

    # ---- وظائف التشفير ----
    def encrypt(self, data: str) -> str:
        return cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return cipher.decrypt(encrypted_data.encode()).decode()

    # ---- إدارة المستخدمين ----
    def get_user(self, telegram_id: int) -> Optional[User]:
        session = self.Session()
        try:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدم: {e}")
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
            logger.error(f"خطأ في إضافة مستخدم: {e}")
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
            logger.error(f"خطأ في تحديث المستخدم: {e}")
            return False
        finally:
            session.close()

    # ---- إدارة اتصالات المنصات ----
    def validate_exchange_credentials(self, platform: str, api_key: str, api_secret: str, passphrase: str = None) -> bool:
        try:
            exchange_class = getattr(ccxt, platform)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'password': passphrase,
                'enableRateLimit': True
            })
            exchange.fetch_balance()  # اختبار الاتصال
            return True
        except Exception as e:
            logger.error(f"خطأ في التحقق من صحة بيانات {platform}: {e}")
            return False

    def add_exchange_connection(self, user_id: int, platform: str, api_key: str, api_secret: str, passphrase: str = None) -> bool:
        session = self.Session()
        try:
            # التحقق من صحة البيانات أولاً
            if not self.validate_exchange_credentials(platform, api_key, api_secret, passphrase):
                return False

            connection = ExchangeConnection(
                user_id=user_id,
                platform=platform,
                api_key=self.encrypt(api_key),
                api_secret=self.encrypt(api_secret),
                passphrase=self.encrypt(passphrase) if passphrase else None,
                is_valid=True
            )
            session.add(connection)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إضافة اتصال منصة: {e}")
            return False
        finally:
            session.close()

    def get_user_connections(self, user_id: int) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            connections = session.query(ExchangeConnection).filter_by(user_id=user_id).all()
            return [
                {
                    'id': conn.id,
                    'platform': conn.platform.value,
                    'is_active': conn.is_active,
                    'is_valid': conn.is_valid
                }
                for conn in connections
            ]
        except Exception as e:
            logger.error(f"خطأ في جلب اتصالات المستخدم: {e}")
            return []
        finally:
            session.close()

    def toggle_connection_status(self, connection_id: int) -> bool:
        session = self.Session()
        try:
            connection = session.query(ExchangeConnection).get(connection_id)
            if connection:
                connection.is_active = not connection.is_active
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تبديل حالة الاتصال: {e}")
            return False
        finally:
            session.close()

    # ---- إدارة الاستثمار ----
    def set_investment_amount(self, user_id: int, amount: float) -> bool:
        session = self.Session()
        try:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.investment_amount = amount
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تعيين مبلغ الاستثمار: {e}")
            return False
        finally:
            session.close()

    def toggle_trading_mode(self, user_id: int) -> bool:
        session = self.Session()
        try:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.mode = 'demo' if user.mode == 'live' else 'live'
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تبديل وضع التداول: {e}")
            return False
        finally:
            session.close()

    def toggle_trading_status(self, user_id: int) -> bool:
        session = self.Session()
        try:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if user:
                user.is_active = not user.is_active
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تبديل حالة التداول: {e}")
            return False
        finally:
            session.close()

    # ---- إدارة المعاملات ----
    def add_transaction(self, transaction_data: dict) -> bool:
        session = self.Session()
        try:
            transaction = Transaction(**transaction_data)
            session.add(transaction)
            
            # تحديث رصيد المستخدم إذا كانت الصفقة ناجحة
            if transaction_data['status'] == 'completed':
                user = session.query(User).filter_by(telegram_id=transaction_data['user_id']).first()
                if user:
                    if transaction_data['type'] == 'live':
                        user.balance += transaction_data['profit']
                    else:
                        user.demo_balance += transaction_data['profit']
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إضافة معاملة: {e}")
            return False
        finally:
            session.close()

    def get_user_transactions(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            since = datetime.now() - timedelta(days=days)
            transactions = session.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= since
            ).order_by(Transaction.created_at.desc()).all()
            
            return [
                {
                    'id': t.id,
                    'platform': t.platform,
                    'symbol': t.symbol,
                    'amount': t.amount,
                    'profit': t.profit,
                    'type': t.type,
                    'status': t.status,
                    'created_at': t.created_at
                }
                for t in transactions
            ]
        except Exception as e:
            logger.error(f"خطأ في جلب معاملات المستخدم: {e}")
            return []
        finally:
            session.close()

    # ---- إدارة فرص المراجحة ----
    def add_arbitrage_opportunity(self, opportunity_data: dict) -> bool:
        session = self.Session()
        try:
            opportunity = ArbitrageOpportunity(**opportunity_data)
            session.add(opportunity)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في إضافة فرصة مراجحة: {e}")
            return False
        finally:
            session.close()

    def get_recent_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            opportunities = session.query(ArbitrageOpportunity).order_by(
                ArbitrageOpportunity.timestamp.desc()
            ).limit(limit).all()
            
            return [
                {
                    'symbol': o.symbol,
                    'buy_exchange': o.buy_exchange,
                    'sell_exchange': o.sell_exchange,
                    'buy_price': o.buy_price,
                    'sell_price': o.sell_price,
                    'profit_percentage': o.profit_percentage,
                    'timestamp': o.timestamp
                }
                for o in opportunities
            ]
        except Exception as e:
            logger.error(f"خطأ في جلب فرص المراجحة: {e}")
            return []
        finally:
            session.close()

    # ---- وظائف المدير ----
    def get_all_users(self) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            users = session.query(User).all()
            return [
                {
                    'id': u.id,
                    'telegram_id': u.telegram_id,
                    'username': u.username,
                    'mode': u.mode,
                    'investment_amount': u.investment_amount,
                    'is_active': u.is_active,
                    'created_at': u.created_at
                }
                for u in users
            ]
        except Exception as e:
            logger.error(f"خطأ في جلب جميع المستخدمين: {e}")
            return []
        finally:
            session.close()

    def get_active_users_count(self) -> int:
        session = self.Session()
        try:
            return session.query(User).filter_by(is_active=True).count()
        except Exception as e:
            logger.error(f"خطأ في جلب عدد المستخدمين النشطين: {e}")
            return 0
        finally:
            session.close()

    def get_total_profit(self, days: int = 30) -> float:
        session = self.Session()
        try:
            since = datetime.now() - timedelta(days=days)
            total = session.query(func.sum(Transaction.profit)).filter(
                Transaction.status == 'completed',
                Transaction.created_at >= since
            ).scalar()
            return total or 0.0
        except Exception as e:
            logger.error(f"خطأ في حساب إجمالي الأرباح: {e}")
            return 0.0
        finally:
            session.close()
