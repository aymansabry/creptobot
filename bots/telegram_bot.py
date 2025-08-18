import logging
from telegram.ext import Application, CommandHandler
from config import Config

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """معالجة أمر /start"""
    await update.message.reply_text(
        "🚀 بوت المراجحة الآلي يعمل بنجاح!\n"
        "أرسل /connect لربح حساب التبادل"
    )

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    try:
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # إعداد معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        
        # بدء البوت
        logger.info("Starting bot...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")

if __name__ == '__main__':
    main()