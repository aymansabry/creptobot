import os
from decouple import config

class Config:
    TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
    BINANCE_API_KEY = config('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = config('BINANCE_SECRET_KEY')
    DATABASE_URL = config('DATABASE_URL', default='sqlite:///database.db')
    OWNER_WALLET = config('OWNER_WALLET')
    DEFAULT_LANGUAGE = config('DEFAULT_LANGUAGE', default='ar')
    
    MIN_INVESTMENT = 1  # 1 USDT
    MIN_PROFIT_PERCENT = 3  # 3%
    BOT_FEE_PERCENT = 1  # 1%
    
    SUPPORTED_CURRENCIES = ['USDT', 'BTC', 'ETH', 'BNB', 'SOL', 'XRP']
