# project_root/core/config.py (Modified)
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
SIMULATE = os.getenv('SIMULATE', 'true').lower() == 'true'
MIN_TRADE_USDT = float(os.getenv('MIN_TRADE_USDT', '1'))
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', '0'))
POLL_INTERVAL = float(os.getenv('POLL_INTERVAL', '5'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MIN_PROFIT_PCT = float(os.getenv('MIN_PROFIT_PCT', '0.3'))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN is required in .env file.')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL is required in .env file.')
# The following lines have been commented out to disable the key check:
# if not ENCRYPTION_KEY:
#     raise RuntimeError('ENCRYPTION_KEY is required in .env file. Use `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())` to generate one.')
