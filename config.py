import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

class Config:
    USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
    OWNER_BOT_TOKEN = os.getenv("OWNER_BOT_TOKEN")
    
    # تعديل هنا لضبط تنسيق رابط قاعدة البيانات
    raw_db_url = os.getenv("DATABASE_URL")
    if raw_db_url and raw_db_url.startswith("mysql://"):
        DATABASE_URL = raw_db_url.replace("mysql://", "mysql+pymysql://")
    else:
        DATABASE_URL = raw_db_url
    
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None  # إضافة هذا السطر
    MIN_INVESTMENT = float(os.getenv("MIN_INVESTMENT", 10.0))