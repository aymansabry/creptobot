# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CRYPTO_API_KEY = os.getenv("CRYPTO_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_WALLET = os.getenv("OWNER_WALLET")
PROFIT_PERCENTAGE = float(os.getenv("PROFIT_PERCENTAGE", 5.0))  # النسبة المئوية للربح
MIN_INVEST_AMOUNT = float(os.getenv("MIN_INVEST_AMOUNT", 10.0))  # الحد الأدنى للاستثمار
MAX_INVEST_AMOUNT = float(os.getenv("MAX_INVEST_AMOUNT", 10000.0))  # الحد الأقصى للاستثمار
