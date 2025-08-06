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
    TRONGRID_API_KEY = config("TRONGRID_API_KEY")  # احصل عليه من trangrid.io
    TRON_USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    
    # Security
    ENCRYPTION_KEY = config("ENCRYPTION_KEY")
    
    # Database
    DB_URL = config("DATABASE_URL")

   
config = Config()
