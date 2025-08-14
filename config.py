import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")  # MySQL
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456))
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")  # مفتاح Fernet للتشفير