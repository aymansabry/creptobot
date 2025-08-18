import logging
from cryptography.fernet import Fernet, InvalidToken
from config import Config
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        self.engine = db.create_engine(Config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.cipher = Fernet(Config.FERNET_KEY)

    def get_user_credentials(self, user_id):
        session = self.Session()
        try:
            user = session.execute(
                db.text("SELECT api_key, api_secret, trade_percent, is_active FROM users WHERE id = :user_id"),
                {'user_id': user_id}
            ).fetchone()
            
            if not user:
                logger.warning(f"No user found with ID: {user_id}")
                return None
                
            try:
                return {
                    'api_key': self.cipher.decrypt(user.api_key.encode()).decode(),
                    'secret_key': self.cipher.decrypt(user.api_secret.encode()).decode(),
                    'trade_percent': user.trade_percent or Config.TRADE_PERCENT,
                    'is_active': user.is_active
                }
            except InvalidToken:
                logger.error(f"Failed to decrypt credentials for user: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Database error for user {user_id}: {str(e)}")
            return None
        finally:
            session.close()

    def update_user_credentials(self, user_id, api_key, api_secret):
        session = self.Session()
        try:
            encrypted_api_key = self.cipher.encrypt(api_key.encode()).decode()
            encrypted_api_secret = self.cipher.encrypt(api_secret.encode()).decode()
            
            session.execute(
                db.text("""
                INSERT INTO users (id, api_key, api_secret, is_active)
                VALUES (:user_id, :api_key, :api_secret, TRUE)
                ON CONFLICT (id) DO UPDATE
                SET api_key = EXCLUDED.api_key,
                    api_secret = EXCLUDED.api_secret,
                    updated_at = CURRENT_TIMESTAMP
                """),
                {
                    'user_id': user_id,
                    'api_key': encrypted_api_key,
                    'api_secret': encrypted_api_secret
                }
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update credentials for user {user_id}: {str(e)}")
            return False
        finally:
            session.close()