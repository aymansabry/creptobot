import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID')) if os.getenv('OWNER_ID') else None
DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
WEB_USERNAME = os.getenv('WEB_USERNAME')
WEB_PASSWORD = os.getenv('WEB_PASSWORD')
FERNET_KEY = os.getenv('FERNET_KEY')
MODE = os.getenv('MODE', 'DRY').upper()
DEFAULT_EXCHANGE = os.getenv('DEFAULT_EXCHANGE', 'binance')

if not FERNET_KEY:
    raise RuntimeError('FERNET_KEY missing in .env — generate with cryptography.Fernet.generate_key()')
