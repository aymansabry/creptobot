import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
MIN_INVESTMENT_USDT = float(os.getenv("MIN_INVESTMENT_USDT", "1"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in .env")
