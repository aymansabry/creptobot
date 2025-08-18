import os
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # OpenAI
    OPENAI_API = os.getenv('OPENAI_API')
    
    # Encryption
    FERNET_KEY = os.getenv('FERNET_KEY')
    
    # Trading Parameters
    BOT_PERCENT = float(os.getenv('BOT_PERCENT', '1.0'))
    MIN_INVEST = float(os.getenv('MIN_INVEST_AMOUNT', '10.0'))
    MAX_INVEST = float(os.getenv('MAX_INVEST_AMOUNT', '1000.0'))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    @classmethod
    def validate(cls):
        required = ['BOT_TOKEN', 'OPENAI_API', 'FERNET_KEY', 'DATABASE_URL']
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            error_msg = f"Missing env vars: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            Fernet(cls.FERNET_KEY)  # Validate encryption key
        except Exception as e:
            logger.error(f"Invalid FERNET_KEY: {str(e)}")
            raise

Config.validate()