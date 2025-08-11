import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

# إنشاء مفتاح تشفير إذا لم يكن موجوداً
if not os.getenv("ENCRYPTION_KEY"):
    key = Fernet.generate_key()
    with open('.env', 'a') as f:
        f.write(f"\nENCRYPTION_KEY={key.decode()}")

class Config:
    # توكنات البوت
    USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
    OWNER_BOT_TOKEN = os.getenv("OWNER_BOT_TOKEN")
    
    # إعدادات قاعدة البيانات
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    
    # إعدادات التشفير
    CIPHER = Fernet(os.getenv("ENCRYPTION_KEY"))
    
    # إعدادات المدير
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    
    # الحد الأدنى للاستثمار
    MIN_INVESTMENT = float(os.getenv("MIN_INVESTMENT", 10.0))
