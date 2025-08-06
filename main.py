import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from core.config import config
from menus.user.main_menu import show_main_menu

# تكوين السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    await show_main_menu(update)

def main():
    if not config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN غير مضبوط!")
        return

    try:
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        
        # معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
        
        logger.info("🤖 جاري تشغيل البوت...")
        application.run_polling()
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {str(e)}")

if __name__ == '__main__':
    main()
