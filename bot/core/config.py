import os
from dotenv import load_dotenv
from typing import Optional

class Settings:
    def __init__(self):
        load_dotenv()
        self.TELEGRAM_TOKEN = self._get_env('TELEGRAM_TOKEN')
        self.DATABASE_URL = self._fix_db_url(self._get_env('DATABASE_URL', 'sqlite:///db.sqlite3'))
        
    def _get_env(self, key: str, default: Optional[str] = None) -> str:
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Missing required environment variable: {key}")
        return value
        
    def _fix_db_url(self, url: str) -> str:
        return url.replace('postgres://', 'postgresql://') if url.startswith('postgres://') else url

settings = Settings()
