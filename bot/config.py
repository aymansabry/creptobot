import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    # تأكد من استخدام PostgreSQL على Railway
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
