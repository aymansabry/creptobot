import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
FERNET_KEY = os.getenv("FERNET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # أضف هذا السطر

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in environment variables")

if not OWNER_ID:
    raise RuntimeError("OWNER_ID missing in environment variables")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing in environment variables")

if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY missing in environment variables — generate with cryptography.Fernet.generate_key()")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing in environment variables")  # تحقق من وجود المفتاح