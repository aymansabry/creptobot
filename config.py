# config.py
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# قاعدة البيانات MySQL
DATABASE_URL = os.getenv("DATABASE_URL")  # صيغة: mysql+mysqlconnector://user:pass@host/dbname

# إعدادات افتراضية
DEFAULT_BOT_FEE_PERCENT = float(os.getenv("BOT_FEE_PERCENT", "10"))
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "false").lower() == "true"

# تحقق أن القيم الأساسية موجودة
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في ملف .env")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL غير موجود في ملف .env")
