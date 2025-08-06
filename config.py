from decouple import config

class Config:
    BOT_TOKEN = config("BOT_TOKEN")
    BINANCE_API_KEY = config("BINANCE_API_KEY")
    BINANCE_SECRET = config("BINANCE_SECRET")
    TRONGRID_API_KEY = config("TRONGRID_API_KEY")
    ADMIN_WALLET = config("ADMIN_WALLET")
    ENCRYPTION_KEY = config("ENCRYPTION_KEY")
    DB_URL = config("DATABASE_URL")

config = Config()
