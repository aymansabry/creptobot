import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# TRON
TRON_API_KEY = os.getenv("TRON_API_KEY")
TRON_MANAGER_WALLET = os.getenv("TRON_MANAGER_WALLET")
TRON_MANAGER_PRIVATE_KEY = os.getenv("TRON_MANAGER_PRIVATE_KEY")

# OpenAI / HF
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database
POSTGRES_URI = os.getenv("POSTGRES_URI")
