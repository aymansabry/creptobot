from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Investment(Base):
    __tablename__ = 'investments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("تم تهيئة قاعدة البيانات بنجاح")

    # ---- وظائف إدارة الاستثمار ----
    def set_investment(self, user_id: int, amount: float) -> bool:
        session = self.Session()
        try:
            investment = session.query(Investment).filter_by(user_id=user_id).first()
            if investment:
                investment.amount = amount
            else:
                investment = Investment(user_id=user_id, amount=amount)
                session.add(investment)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في حفظ الاستثمار: {e}")
            return False
        finally:
            session.close()

    def get_investment(self, user_id: int) -> dict:
        session = self.Session()
        try:
            investment = session.query(Investment).filter_by(user_id=user_id).first()
            return {
                'amount': investment.amount if investment else 0.0,
                'is_active': investment.is_active if investment else False
            }
        except Exception as e:
            logger.error(f"خطأ في جلب بيانات الاستثمار: {e}")
            return {'amount': 0.0, 'is_active': False}
        finally:
            session.close()

    def toggle_investment(self, user_id: int) -> bool:
        session = self.Session()
        try:
            investment = session.query(Investment).filter_by(user_id=user_id).first()
            if investment:
                investment.is_active = not investment.is_active
                session.commit()
                return investment.is_active
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"خطأ في تبديل حالة الاستثمار: {e}")
            return False
        finally:
            session.close()
