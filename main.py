import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
import handlers
import database

# تحميل متغيرات البيئة
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # mysql://user:pass@host/dbname

if not TOKEN:
    raise ValueError("❌ يجب تعيين TELEGRAM_BOT_TOKEN في ملف .env")

if not DATABASE_URL:
    raise ValueError("❌ يجب تعيين DATABASE_URL في ملف .env")

# تهيئة تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات
database.init_db()

def main():
    # بناء تطبيق البوت
    application = ApplicationBuilder().token(TOKEN).build()

    # تسجيل المعالجات
    handlers.register_handlers(application)

    logger.info("🚀 البوت شغال...")
    application.run_polling()

if __name__ == "__main__":
    main()
