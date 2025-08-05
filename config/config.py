# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

OWNER_WALLET_ADDRESS = os.getenv("OWNER_WALLET_ADDRESS")
BOT_PROFIT_PERCENTAGE = float(os.getenv("BOT_PROFIT_PERCENTAGE", 3.0))
