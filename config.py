import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

class Config:
    USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
    OWNER_BOT_TOKEN = os.getenv("OWNER_BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    MIN_INVESTMENT = float(os.getenv("MIN_INVESTMENT", 10.0))
