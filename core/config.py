import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite3")

OWNER_IDS = [int(id_) for id_ in os.getenv("OWNER_IDS", "").split(",") if id_]
