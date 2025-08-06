from decouple import config

class Config:
    # Telegram
    BOT_TOKEN = config("BOT_TOKEN")
    
    # Binance
    BINANCE_API_KEY = config("BINANCE_API_KEY", default="")
    BINANCE_API_SECRET = config("BINANCE_API_SECRET", default="")
    
    # Database
    DB_URL = config("DATABASE_URL", default="sqlite+aiosqlite:///database.db")
    
    # Deployment
    DEPLOY_MODE = config("DEPLOY_MODE", default="polling")
    WEBHOOK_URL = config("WEBHOOK_URL", default="")
    PORT = int(config("PORT", default=8000))
    # إعدادات جديدة لمنع التضارب
    BOT_LOCK_TIMEOUT = int(config("BOT_LOCK_TIMEOUT", default=5))  # ثواني
    MAX_RETRIES = int(config("MAX_RETRIES", default=3))

config = Config()
