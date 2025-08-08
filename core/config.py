# project_root/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """
    Class to hold application settings.
    It loads environment variables from a .env file.
    """
    
    # Telegram Bot Token
    BOT_TOKEN: str
    
    # Database URL for PostgreSQL (Railway provides this automatically)
    DATABASE_URL: str
    
    # API Keys for Binance
    BINANCE_API_KEY: str
    BINANCE_SECRET_KEY: str
    
    # API Keys for KuCoin
    KUCOIN_API_KEY: str
    KUCOIN_SECRET_KEY: str
    KUCOIN_PASS_PHRASE: str
    
    # OpenAI API Key
    OPENAI_API_KEY: str
    
    # The Admin Telegram User ID (used for notifications)
    ADMIN_ID: int

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()
