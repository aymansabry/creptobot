# project_root/core/config.py

import os

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

settings = Settings()
