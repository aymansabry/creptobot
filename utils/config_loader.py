# utils/config_loader.py
import os
from dotenv import load_dotenv
from typing import Dict, Any
import redis

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
        
        # فحص وجود نسخة أخرى تعمل
        self._check_duplicate_instance()

    def _check_duplicate_instance(self):
        """فحص وجود نسخة أخرى من البوت تعمل"""
        redis_client = redis.from_url(self.get('redis.url'))
        lock_key = f"bot_lock:{self.get('telegram.bot_token')}"
        
        # محاولة الحصول على قفل لمدة 60 ثانية
        acquired = redis_client.set(lock_key, "1", nx=True, ex=60)
        if not acquired:
            raise RuntimeError("Another instance of the bot is already running")

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
