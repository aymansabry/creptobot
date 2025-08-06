from decouple import config

class Config:
    # Binance
    BINANCE_API_KEY = config("REAL_BINANCE_API_KEY")
    BINANCE_SECRET = config("REAL_BINANCE_SECRET")
    
    # Tron
    TRON_PRIVATE_KEY = config("ENCRYPTED_TRON_KEY")  # مشفرة
    ADMIN_WALLET = config("ADMIN_TRON_WALLET")
    
    # Security
    ENCRYPTION_KEY = config("ENCRYPTION_MASTER_KEY")
    ALLOWED_USERS = [int(u) for u in config("ALLOWED_USER_IDS").split(",")]

config = Config()
