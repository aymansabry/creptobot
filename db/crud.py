from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session
from config import Config
from .models import User
import logging

logger = logging.getLogger(__name__)

cipher = Fernet(Config.FERNET_KEY)

class CRUDUser:
    @staticmethod
    def get_user(db: Session, user_id: int):
        """استرجاع مستخدم بواسطة ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_or_update_user(
        db: Session,
        user_id: int,
        api_key: str,
        api_secret: str,
        trade_percent: float = None
    ):
        """إنشاء أو تحديث مستخدم"""
        try:
            encrypted_api_key = cipher.encrypt(api_key.encode()).decode()
            encrypted_api_secret = cipher.encrypt(api_secret.encode()).decode()
            
            user = CRUDUser.get_user(db, user_id)
            
            if user:
                user.api_key = encrypted_api_key
                user.api_secret = encrypted_api_secret
                if trade_percent:
                    user.trade_percent = trade_percent
            else:
                user = User(
                    id=user_id,
                    api_key=encrypted_api_key,
                    api_secret=encrypted_api_secret,
                    trade_percent=trade_percent or Config.TRADE_PERCENT
                )
                db.add(user)
            
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error in create_or_update_user: {str(e)}")
            raise

    @staticmethod
    def get_user_credentials(db: Session, user_id: int):
        """استرجاع مفاتيح مستخدم مع فك التشفير"""
        user = CRUDUser.get_user(db, user_id)
        if not user:
            return None
            
        try:
            return {
                'api_key': cipher.decrypt(user.api_key.encode()).decode(),
                'secret_key': cipher.decrypt(user.api_secret.encode()).decode(),
                'trade_percent': user.trade_percent,
                'is_active': user.is_active
            }
        except InvalidToken:
            logger.error(f"Invalid token for user {user_id}")
            return None

    @staticmethod
    def update_trade_percent(db: Session, user_id: int, percent: float):
        """تحديث نسبة التداول للمستخدم"""
        user = CRUDUser.get_user(db, user_id)
        if not user:
            return False
            
        try:
            user.trade_percent = percent
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating trade percent: {str(e)}")
            return False