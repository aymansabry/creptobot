from telegram.ext import Application
from config import Config
from handlers import setup_handlers
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    """المهام التي تنفذ بعد التهيئة"""
    # هنا يمكنك إضافة أي إعدادات أولية
    logger.info("Bot initialization completed")

def main():
    """تشغيل البوت"""
    application = Application.builder()\
                            .token(Config.TELEGRAM_TOKEN)\
                            .post_init(post_init)\
                            .build()
    
    # إعداد المعالجات
    setup_handlers(application)
    
    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()
