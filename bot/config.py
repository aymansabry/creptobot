import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    # Binance API
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    
    # Database (Railway provides this automatically)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # App Settings
    OWNER_WALLET = os.getenv('OWNER_WALLET')
    MIN_INVESTMENT = float(os.getenv('MIN_INVESTMENT', 1.0))
    BOT_FEE_PERCENT = float(os.getenv('BOT_FEE_PERCENT', 1.0))
