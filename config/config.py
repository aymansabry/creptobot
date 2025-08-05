import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات التليجرام
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS').split(',')]
    
    # إعدادات قاعدة البيانات
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    
    # إعدادات بينانس
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    
    # إعدادات أخرى
    COMMISSION_RATE = float(os.getenv('COMMISSION_RATE', 0.05))  # 5%
    MIN_INVESTMENT = float(os.getenv('MIN_INVESTMENT', 1.0))    # 1 USDT
