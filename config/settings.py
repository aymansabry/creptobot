import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ADMIN_IDS: list = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
    
    # إعدادات الذكاء الاصطناعي
    AI_API_KEY: str = os.getenv("AI_API_KEY")
    AI_MODEL: str = "gpt-4"
    
    # إعدادات بينانس
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY")
    
    class Config:
        env_file = ".env"

settings = Settings()
