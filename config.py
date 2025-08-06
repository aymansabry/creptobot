from decouple import config

class Config:
    # Telegram
    BOT_TOKEN = config("BOT_TOKEN")
    
    # Binance
    BINANCE_API_KEY = config("BINANCE_API_KEY")
    BINANCE_SECRET = config("BINANCE_SECRET")
    BINANCE_API_URL = config("BINANCE_API_URL", "https://api.binance.com")
    
    # Tron
    TRONGRID_API_URL = "https://api.trongrid.io"
    TRON_USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    TRON_PRIVATE_KEY = config("TRON_PRIVATE_KEY")
    ADMIN_WALLET = config("ADMIN_WALLET")
    
    # Security
    ENCRYPTION_KEY = config("ENCRYPTION_KEY")
    
    # Database
    DB_URL = config("DATABASE_URL")

config = Config()
