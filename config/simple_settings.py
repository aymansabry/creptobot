import os
from typing import List

class Settings:
    def __init__(self):
        # التحقق من وجود المتغيرات الأساسية
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'DATABASE_URL',
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY',
            'AI_API_KEY'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"مفقود: {', '.join(missing)}")

        # تحميل الإعدادات
        self.BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
        self.BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
        self.AI_API_KEY = os.getenv('AI_API_KEY')
        self.ADMIN_IDS = [int(i) for i in os.getenv('ADMIN_IDS', '').split(',') if i]

settings = Settings()
