from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Telegram Bot Settings
    BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    ADMIN_IDS: List[int] = Field(default_factory=lambda: list(map(int, os.getenv("ADMIN_IDS", "").split(","))))
    
    # Database Settings
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")
    
    # Binance API
    BINANCE_API_KEY: str = Field(..., env="BINANCE_API_KEY")
    BINANCE_SECRET_KEY: str = Field(..., env="BINANCE_SECRET_KEY")
    
    # AI Settings
    AI_API_KEY: str = Field(..., env="AI_API_KEY")
    AI_MODEL: str = "gpt-4"
    
    # Risk Management
    MAX_RISK_SCORE: float = 0.3
    MAX_TRADE_AMOUNT: float = 10000
    MIN_TRADE_AMOUNT: float = 1
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
