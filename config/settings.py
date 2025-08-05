from pydantic import BaseModel, PostgresDsn
from typing import List
import os

class Settings(BaseModel):
    BOT_TOKEN: str = ""
    ADMIN_IDS: List[int] = []
    DATABASE_URL: PostgresDsn = ""
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4"

def load_settings():
    try:
        admin_ids = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()]
        
        return Settings(
            BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            ADMIN_IDS=admin_ids,
            DATABASE_URL=os.getenv("DATABASE_URL", ""),
            BINANCE_API_KEY=os.getenv("BINANCE_API_KEY", ""),
            BINANCE_SECRET_KEY=os.getenv("BINANCE_SECRET_KEY", ""),
            AI_API_KEY=os.getenv("AI_API_KEY", "")
        )
    except Exception as e:
        raise ValueError(f"فشل تحميل الإعدادات: {str(e)}")

settings = load_settings()
