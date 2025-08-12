# config.py
import os

# إعدادات قاعدة البيانات MySQL
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "bot_db")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")

# بيئة العمل: production أو sandbox
USE_SANDBOX = os.getenv("USE_SANDBOX", "false").lower() == "true"

# نسبة الربح الافتراضية
DEFAULT_BOT_FEE_PERCENT = 10.0

# منصات التداول المدعومة
SUPPORTED_EXCHANGES = ["binance", "kucoin"]

# إعدادات أخرى
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
