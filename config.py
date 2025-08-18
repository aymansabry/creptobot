import os
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # إعدادات أساسية
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    FERNET_KEY = os.getenv('FERNET_KEY')
    
    # إعدادات التداول
    TRADE_PERCENT = float(os.getenv('BOT_PERCENT', '1.0'))
    MIN_INVEST = float(os.getenv('MIN_INVEST_AMOUNT', '10.0'))
    MAX_INVEST = float(os.getenv('MAX_INVEST_AMOUNT', '1000.0'))
    
    # إعدادات المراجحة
    ARB_THRESHOLD = float(os.getenv('ARB_THRESHOLD', '0.5'))  # نسبة المراجحة المطلوبة
    EXCHANGES = ['binance', 'kucoin', 'bybit']  # المنصات المدعومة
    
    @staticmethod
    def validate():
        required = ['BOT_TOKEN', 'FERNET_KEY']
        missing = [var for var in required if not getattr(Config, var)]
        if missing:
            raise ValueError(f'Missing required config: {missing}')

Config.validate()