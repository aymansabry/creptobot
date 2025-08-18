import os
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # Telegram Configuration
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Encryption
    FERNET_KEY = os.getenv('FERNET_KEY')
    
    # Trading Parameters
    TRADE_PERCENT = float(os.getenv('BOT_PERCENT', '1.0'))  # Default 1%
    MIN_INVEST_AMOUNT = float(os.getenv('MIN_INVEST_AMOUNT', '10.0'))
    MAX_INVEST_AMOUNT = float(os.getenv('MAX_INVEST_AMOUNT', '1000.0'))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    @classmethod
    def validate(cls):
        required_vars = {
            'TELEGRAM_BOT_TOKEN': 'Telegram Bot Token',
            'OPENAI_API_KEY': 'OpenAI API Key',
            'FERNET_KEY': 'Fernet Encryption Key',
            'DATABASE_URL': 'Database Connection URL'
        }
        
        missing = [name for name, desc in required_vars.items() if not os.getenv(name)]
        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            Fernet(cls.FERNET_KEY)
        except Exception as e:
            logger.error(f"Invalid FERNET_KEY: {str(e)}")
            raise

Config.validate()