import asyncio
import logging
import os
from telegram.ext import ApplicationBuilder
from database import init_db  # ✅ تم التصحيح
from handlers import setup_handlers

# إعداد تسجيل الأحداث (الـ logs)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# جلب التوكن من متغير البيئة
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ لم يتم ضبط متغير TELEGRAM_BOT_TOKEN في البيئة.")

# الدالة الرئيسية
async def main():
    # إنشاء التطبيق
    app = ApplicationBuilder().token(TOKEN).build()

    # تهيئة قاعدة البيانات
    await init_db()

    # إعداد الهاندلرز (الأوامر، الأزرار، الخ)
    setup_handlers(app)

    logger.info("✅ البوت يعمل الآن...")

    # تشغيل البوت
    await app.run_polling()

# تشغيل الدالة الرئيسية
if __name__ == "__main__":
    asyncio.run(main())
