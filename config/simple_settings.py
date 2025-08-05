import os
from typing import List

class Settings:
    def __init__(self):
        # قائمة بالمتغيرات المطلوبة
        self.REQUIRED_VARS = [
            'TELEGRAM_BOT_TOKEN',
            'DATABASE_URL',
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY',
            'AI_API_KEY'
        ]
        
        self.check_required_vars()
        self.load_settings()
        self.validate_settings()

    def check_required_vars(self):
        """التحقق من وجود المتغيرات المطلوبة"""
        missing = [var for var in self.REQUIRED_VARS if not os.getenv(var)]
        if missing:
            raise ValueError(f"المتغيرات المطلوبة مفقودة: {', '.join(missing)}")

    def load_settings(self):
        """تحميل جميع الإعدادات"""
        # الإعدادات الأساسية
        self.BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
        self.BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
        self.AI_API_KEY = os.getenv('AI_API_KEY')
        
        # الإعدادات الاختيارية
        self.ADMIN_IDS = self.parse_admin_ids(os.getenv('ADMIN_IDS', ''))
        self.AI_MODEL = os.getenv('AI_MODEL', 'gpt-4')

    def parse_admin_ids(self, ids_str: str) -> List[int]:
        """تحويل ADMIN_IDS من نص إلى قائمة أرقام"""
        try:
            return [int(i.strip()) for i in ids_str.split(',') if i.strip()]
        except ValueError:
            return []

    def validate_settings(self):
        """التحقق من صحة الإعدادات"""
        if not self.BOT_TOKEN.startswith(''):
            raise ValueError("توكن البوت غير صحيح")
        
        if not self.DATABASE_URL.startswith('postgresql'):
            raise ValueError("رابط قاعدة البيانات غير صحيح")

settings = Settings()
