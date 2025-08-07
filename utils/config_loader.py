# utils/config_loader.py
import os
from dotenv import load_dotenv
from typing import Dict, Any
import redis
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self):
        load_dotenv()
        self.config = {
            'binance': {
                'api_key': os.getenv('BINANCE_API_KEY'),
                'api_secret': os.getenv('BINANCE_API_SECRET')
            },
            'kucoin': {
                'api_key': os.getenv('KUCOIN_API_KEY'),
                'api_secret': os.getenv('KUCOIN_API_SECRET')
            },
            'database': {
                'url': os.getenv('DATABASE_URL')
            },
            'telegram': {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'admin_ids': [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
            },
            'trading': {
                'min_trade_amount': float(os.getenv('MIN_TRADE_AMOUNT', 1.0)),
                'bot_commission': float(os.getenv('BOT_COMMISSION', 0.1)),
                'risk_threshold': float(os.getenv('RISK_THRESHOLD', 0.3)),
                'main_wallet_address': os.getenv('MAIN_WALLET_ADDRESS'),
                'owner_tron_address': os.getenv('OWNER_TRON_ADDRESS')
            },
            'redis': {
                'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            }
        }
        
        # فحص اتصال Redis مع معالجة الأخطاء
        self._check_redis_connection()

    def _check_redis_connection(self):
        """فحص اتصال Redis مع تجاوز الخطأ إذا فشل الاتصال"""
        try:
            redis_client = redis.from_url(self.get('redis.url'))
            redis_client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {str(e)}")
            # تعطيل ميزة التحقق من النسخ المكررة إذا فشل الاتصال
            self.config['redis']['disabled'] = True

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default
    
    def get_all(self) -> Dict:
        return self.config
