ffrom pydantic import BaseModel, PostgresDsn
from typing import List
import os

class Settings(BaseModel):
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = []
    DATABASE_URL: PostgresDsn
    BINANCE_API_KEY: str
    BINANCE_SECRET_KEY: str
    AI_API_KEY: str
    AI_MODEL: str = "gpt-4"
    MAX_RISK_SCORE: float = 0.3
    MAX_TRADE_AMOUNT: float = 10000
    MIN_TRADE_AMOUNT: float = 1

def load_settings():
    # معالجة ADMIN_IDS يدوياً
    admin_ids = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i]
    
    return Settings(
        BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN"),
        ADMIN_IDS=admin_ids,
        DATABASE_URL=os.getenv("DATABASE_URL"),
        BINANCE_API_KEY=os.getenv("BINANCE_API_KEY"),
        BINANCE_SECRET_KEY=os.getenv("BINANCE_SECRET_KEY"),
        AI_API_KEY=os.getenv("AI_API_KEY")
    )

settings = load_settings()
