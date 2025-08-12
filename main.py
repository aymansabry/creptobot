# main.py
import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder

import handlers
import database

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # mysql://user:pass@host/dbname

if not TOKEN:
    raise ValueError("خطأ: يجب تعيين TELEGRAM_BOT_TOKEN في ملف .env")

if not DATABASE_URL:
    raise ValueError("خطأ: يجب تعيين DATABASE_URL في ملف .env")

# تهيئة تسجيل الدخول
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات مع الرابط من env
database.init_db(DATABASE_URL)

async def main():
    # بناء تطبيق البوت
    application = ApplicationBuilder().token(TOKEN).build()

    # تسجيل المعالجات
    handlers.register_handlers(application)

    # تشغيل البوت
    logger.info("🚀 البوت شغال...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
