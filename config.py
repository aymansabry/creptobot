from decouple import config

class Config:
    # Telegram
    BOT_TOKEN = config("BOT_TOKEN")
    
    # Binance
    BINANCE_API_KEY = config("BINANCE_API_KEY", default="")
    BINANCE_API_SECRET = config("BINANCE_API_SECRET", default="")
    
    # TRON
    TRONGRID_API_KEY = config("TRONGRID_API_KEY", default="")
    ADMIN_WALLET = config("ADMIN_WALLET", default="")
    
    # Database
    DB_URL = config("DATABASE_URL", default="sqlite+aiosqlite:///database.db")
    
    # Deployment
    DEPLOY_MODE = config("DEPLOY_MODE", default="polling")
    WEBHOOK_URL = config("WEBHOOK_URL", default="")
    PORT = int(config("PORT", default=8000))
    
    # Admins
    ADMINS = list(map(int, config("ADMINS", default="").split(","))) if config("ADMINS", default="") else []
    
    @property
    def is_production(self):
        return self.DEPLOY_MODE == "webhook" and bool(self.WEBHOOK_URL)
   
    # إعدادات جديدة لمنع التضارب
    BOT_LOCK_TIMEOUT = int(config("BOT_LOCK_TIMEOUT", default=10))  # ثواني
    MAX_CONFLICT_RETRIES = int(config("MAX_CONFLICT_RETRIES", default=5))

config = Config()
