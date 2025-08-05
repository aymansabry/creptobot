from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import List
import os

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    ADMIN_IDS: List[int] = Field(default=[], env="ADMIN_IDS")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")
    
    # Binance
    BINANCE_API_KEY: str = Field(..., env="BINANCE_API_KEY")
    BINANCE_SECRET_KEY: str = Field(..., env="BINANCE_SECRET_KEY")
    
    # AI
    AI_API_KEY: str = Field(..., env="AI_API_KEY")
    AI_MODEL: str = "gpt-4"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

def parse_admin_ids():
    admin_ids = os.getenv("ADMIN_IDS", "")
    return [int(id.strip()) for id in admin_ids.split(",") if id.strip()]

settings = Settings()
settings.ADMIN_IDS = parse_admin_ids()
