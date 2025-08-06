from decouple import config
from typing import List

class Config:
    # Telegram
    BOT_TOKEN = config("BOT_TOKEN")
    
    # Binance
    BINANCE_API_KEY = config("BINANCE_API_KEY")
    BINANCE_API_SECRET = config("BINANCE_SECRET")
    
    # Tron
    TRON_PRIVATE_KEY = config("TRON_PRIVATE_KEY")
    ADMIN_WALLET = config("ADMIN_WALLET")
    
    # Security
    ENCRYPTION_KEY = config("ENCRYPTION_KEY")
    
    # Settings
    ALLOWED_USER_IDS = [int(i) for i in config("ALLOWED_USER_IDS", "").split(",") if i]
    MIN_INVESTMENT = float(config("MIN_INVESTMENT", 10.0))

config = Config()
