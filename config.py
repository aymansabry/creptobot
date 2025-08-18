import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات البوت
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    
    # التشفير
    FERNET_KEY = os.getenv('FERNET_KEY')
    
    # التداول
    MAX_TRADE = float(os.getenv('MAX_TRADE', 5000))
    MIN_TRADE = float(os.getenv('MIN_TRADE', 1))
    BOT_PERCENT = float(os.getenv('BOT_PERCENT', 0.003))
    BOT_WALLET = os.getenv('BOT_WALLET')
    
    # قاعدة البيانات
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # الأمان
    MAX_SLIPPAGE = 0.005
    MIN_PROFIT = 0.002