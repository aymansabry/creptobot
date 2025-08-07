import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")
TRON_PUBLIC_ADDRESS = os.getenv("TRON_PUBLIC_ADDRESS")
BOT_COMMISSION_WALLET = os.getenv("BOT_COMMISSION_WALLET")

POSTGRES_URI = os.getenv("POSTGRES_URI")

ADMIN_IDS = [int(uid) for uid in os.getenv("ADMIN_IDS", "").split(",") if uid]
