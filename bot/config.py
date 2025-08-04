import os
from decouple import config

class Config:
    # إعدادات بوت التليجرام
    TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
    
    # إعدادات بينانس
    BINANCE_API_KEY = config('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = config('BINANCE_SECRET_KEY')
    
    # إعدادات قاعدة البيانات
    DATABASE_URL = config('DATABASE_URL', default='sqlite:///database.db')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # إعدادات أخرى
    OWNER_WALLET = config('OWNER_WALLET')
    DEFAULT_LANGUAGE = config('DEFAULT_LANGUAGE', default='ar')
    MIN_INVESTMENT = config('MIN_INVESTMENT', default=1.0, cast=float)
    MIN_PROFIT_PERCENT = config('MIN_PROFIT_PERCENT', default=3.0, cast=float)
    BOT_FEE_PERCENT = config('BOT_FEE_PERCENT', default=1.0, cast=float)
