# project_root/core/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    # Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Admin User ID
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

    # OpenAI API Key for AI insights
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    # Exchange API Keys
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY")
    KUCOIN_API_KEY: str = os.getenv("KUCOIN_API_KEY")
    KUCOIN_SECRET_KEY: str = os.getenv("KUCOIN_SECRET_KEY")
    KUCOIN_PASSPHRASE: str = os.getenv("KUCOIN_PASSPHRASE")

settings = Settings()
