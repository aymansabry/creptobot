import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

    TRON_API_KEY = os.getenv("TRON_API_KEY")
    TRON_WALLET_ADDRESS = os.getenv("TRON_WALLET_ADDRESS")  # عمولة البوت

    CENTRAL_WALLET_ADDRESS = os.getenv("CENTRAL_WALLET_ADDRESS")  # محفظة المستثمرين المركزية

    MIN_INVEST = float(os.getenv("MIN_INVEST", 10))
    MAX_INVEST = float(os.getenv("MAX_INVEST", 10000))
    BOT_PROFIT_PERCENTAGE = float(os.getenv("BOT_PROFIT_PERCENTAGE", 3))
