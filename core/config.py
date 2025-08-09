import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
KUCOIN_API_KEY = os.getenv("KUCOIN_API_KEY")
KUCOIN_API_SECRET = os.getenv("KUCOIN_API_SECRET")
KUCOIN_API_PASSPHRASE = os.getenv("KUCOIN_API_PASSPHRASE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ENCRYPTION_ENABLED = os.getenv("ENCRYPTION_ENABLED", "False").lower() == "true"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")
MIN_INVESTMENT_USDT = float(os.getenv("MIN_INVESTMENT_USDT", "1"))

BINANCE_ENABLED = os.getenv("BINANCE_ENABLED", "False").lower() == "true"
KUCOIN_ENABLED = os.getenv("KUCOIN_ENABLED", "False").lower() == "true"
