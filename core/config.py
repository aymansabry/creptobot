import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class Config:
    MIN_INVESTMENT = float(os.getenv('MIN_INVESTMENT', '1.0'))
    TRADING_MODE = os.getenv('TRADING_MODE', 'virtual')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    
    # إعدادات الذكاء الاصطناعي
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4')

    # إعدادات Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    @property
    def DB_PARAMS(self):
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return {}
        
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password
        }

config = Config()
