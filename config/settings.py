from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, RedisDsn
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Telegram Bot Settings
    BOT_TOKEN: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    ADMIN_IDS: List[int] = Field(default=[], validation_alias="ADMIN_IDS")
    
    # Database Settings
    DATABASE_URL: PostgresDsn = Field(..., validation_alias="DATABASE_URL")
    
    # Binance API Keys
    BINANCE_API_KEY: str = Field(..., validation_alias="BINANCE_API_KEY")
    BINANCE_SECRET_KEY: str = Field(..., validation_alias="BINANCE_SECRET_KEY")
    
    # AI Settings
    AI_API_KEY: str = Field(..., validation_alias="AI_API_KEY")
    AI_MODEL: str = "gpt-4"
    
    # Risk Management
    MAX_RISK_SCORE: float = 0.3
    MAX_TRADE_AMOUNT: float = 10000
    MIN_TRADE_AMOUNT: float = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

def get_settings():
    # معالجة ADMIN_IDS يدوياً
    admin_ids = os.getenv("ADMIN_IDS", "")
    processed_admin_ids = [int(i.strip()) for i in admin_ids.split(",") if i.strip()]
    
    return Settings(
        ADMIN_IDS=processed_admin_ids,
        BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN"),
        DATABASE_URL=os.getenv("DATABASE_URL"),
        BINANCE_API_KEY=os.getenv("BINANCE_API_KEY"),
        BINANCE_SECRET_KEY=os.getenv("BINANCE_SECRET_KEY"),
        AI_API_KEY=os.getenv("AI_API_KEY")
    )

settings = get_settings()
