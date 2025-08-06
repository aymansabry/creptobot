# config/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
    
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    BINANCE_WALLET_ADDRESS = os.getenv("BINANCE_WALLET_ADDRESS")  # المحفظة المركزية الحقيقية

    OWNER_TRON_WALLET = os.getenv("OWNER_TRON_WALLET")  # محفظة أرباح المالك على شبكة TRON

    AI_API_KEY = os.getenv("AI_API_KEY")  # مفتاح API للذكاء الاصطناعي

    DB_URL = os.getenv("DATABASE_URL")

    MIN_INVEST_AMOUNT = float(os.getenv("MIN_INVEST_AMOUNT", 50))
    MAX_INVEST_AMOUNT = float(os.getenv("MAX_INVEST_AMOUNT", 10000))

    BOT_PROFIT_PERCENTAGE = float(os.getenv("BOT_PROFIT_PERCENTAGE", 3.0))
