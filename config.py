from decouple import config
from typing import Optional

class Config:
    # Telegram Bot Settings
    BOT_TOKEN: str = config("BOT_TOKEN", default="")
    
    # Binance API Settings
    BINANCE_API_KEY: str = config("BINANCE_API_KEY", default="")
    BINANCE_API_SECRET: str = config("BINANCE_API_SECRET", default="")
    BINANCE_API_URL: str = config("BINANCE_API_URL", default="https://api.binance.com")
    
    # TRON Network Settings
    TRONGRID_API_KEY: str = config("TRONGRID_API_KEY", default="")
    TRONGRID_API_URL: str = config("TRONGRID_API_URL", default="https://api.trongrid.io")
    TRON_USDT_CONTRACT: str = config("TRON_USDT_CONTRACT", 
                                  default="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
    
    # Database Settings
    DB_URL: str = config("DATABASE_URL", 
                       default="sqlite+aiosqlite:///database.db")
    
    # Security Settings
    ENCRYPTION_KEY: str = config("ENCRYPTION_KEY", 
                               default="change-this-to-32-char-secret")
    
    # Deployment Settings
    DEPLOY_MODE: str = config("DEPLOY_MODE", default="polling")  # polling or webhook
    WEBHOOK_URL: Optional[str] = config("WEBHOOK_URL", default=None)
    PORT: int = int(config("PORT", default=8000))
    
    # Trading Parameters
    MIN_INVESTMENT: float = float(config("MIN_INVESTMENT", default=10.0))
    MAX_INVESTMENT: float = float(config("MAX_INVESTMENT", default=5000.0))
    BOT_COMMISSION: float = float(config("BOT_COMMISSION", default=0.015))
    
    @property
    def is_production(self) -> bool:
        return self.DEPLOY_MODE.lower() == "webhook"

# Create config instance
config = Config()
