import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
TRON_WALLET_ADDRESS = os.getenv("TRON_WALLET_ADDRESS")
TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")
OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")
AI_ENGINE_API_KEY = os.getenv("AI_ENGINE_API_KEY")

