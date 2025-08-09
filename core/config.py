import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in .env")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in .env")

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY must be set in .env")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env")
