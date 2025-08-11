import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

class Config:
    USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
    OWNER_BOT_TOKEN = os.getenv("OWNER_BOT_TOKEN")
    
    # معالجة رابط قاعدة البيانات
    raw_db_url = os.getenv("DATABASE_URL", "")
    DATABASE_URL = raw_db_url.replace("mysql://", "mysql+pymysql://") if raw_db_url.startswith("mysql://") else raw_db_url
    
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    # معالجة ADMIN_ID بشكل آمن
    try:
        ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # 0 يعني لا يوجد إشعارات
    except (ValueError, TypeError):
        ADMIN_ID = 0
    
    MIN_INVESTMENT = float(os.getenv("MIN_INVESTMENT", 10.0))