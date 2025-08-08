import logging
import os
from telegram.ext import ApplicationBuilder, Application
from src.handlers import setup_handlers
from src.db import init_db

# إعدادات اللوج
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # تهيئة قاعدة البيانات
    init_db()
    print("✅ تم تهيئة قاعدة البيانات")

    # إنشاء التطبيق
    app: Application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    # إعداد جميع الهاندلرز
    setup_handlers(app)
    print("✅ تم إعداد الـ Handlers")

    logger.info("✅ البوت يعمل الآن...")

    # تشغيل البوت بنظام polling
    app.run_polling()

if __name__ == "__main__":
    main()
