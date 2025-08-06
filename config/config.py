import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

    DATABASE_URL = os.getenv("DATABASE_URL")

    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

    OWNER_TRON_WALLET = os.getenv("OWNER_WALLET_ADDRESS")
    CENTRAL_BNB_WALLET = os.getenv("CENTRAL_BNB_WALLET")

    AI_API_KEY = os.getenv("AI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    MIN_INVEST = float(os.getenv("MIN_INVEST", 10))
    MAX_INVEST = float(os.getenv("MAX_INVEST", 10000))

    PROFIT_MARGIN = float(os.getenv("PROFIT_MARGIN", 3))  # percent
    BOT_COMMISSION_PERCENT = float(os.getenv("BOT_COMMISSION_PERCENT", 20))

settings = Settings()
