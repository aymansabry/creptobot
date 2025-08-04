import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN missing in environment variables")

if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
