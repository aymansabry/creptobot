import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY missing in .env — generate with cryptography.Fernet.generate_key()")

fernet = Fernet(FERNET_KEY.encode())

MODE = os.getenv("MODE", "production")  # للإعدادات المختلفة إذا لزم الأمر