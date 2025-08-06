from decouple import config

class Config:
    # الإعدادات الأساسية
    BOT_TOKEN = config("BOT_TOKEN")
    
    # Binance
    BINANCE_API_KEY = config("BINANCE_API_KEY")
    BINANCE_SECRET = config("BINANCE_SECRET")
    
    # TRON (مع قيم افتراضية)
    TRONGRID_API_KEY = config("TRONGRID_API_KEY", default="")  # يمكن تركها فارغة
    TRONGRID_API_URL = config("TRONGRID_API_URL", default="https://api.trongrid.io")
    TRON_USDT_CONTRACT = config("TRON_USDT_CONTRACT", default="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
    
    # أخرى
    ENCRYPTION_KEY = config("ENCRYPTION_KEY", default="dummy-key-for-dev")
    DB_URL = config("DATABASE_URL", default="sqlite+aiosqlite:///db.sqlite3")

config = Config()
