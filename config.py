from decouple import config

class Config:
    # Telegram
    BOT_TOKEN = config("BOT_TOKEN")
    
    # Binance
    BINANCE_API_KEY = config("BINANCE_API_KEY")
    BINANCE_SECRET = config("BINANCE_SECRET")
    BINANCE_API_URL = config("BINANCE_API_URL", "https://api.binance.com")
    
    # Tron
    TRON_PRIVATE_KEY = config("TRON_PRIVATE_KEY")
    ADMIN_WALLET = config("ADMIN_WALLET")
    
    # Security
    ENCRYPTION_KEY = config("ENCRYPTION_KEY")
    
    # Database
    DB_URL = config("DATABASE_URL")

config = Config()
