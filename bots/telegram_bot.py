import logging
from telegram.ext import Updater, CommandHandler
from core.exchanges.binance import BinanceExchange
from config import Config

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    """معالجة أمر /start"""
    update.message.reply_text(
        "🚀 بوت المراجحة الآلي يعمل بنجاح!\n"
        "أرسل /connect لربح حساب التبادل"
    )

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    # تهيئة Updater بدون use_context
    updater = Updater(Config.BOT_TOKEN)
    
    # إعداد معالجات الأوامر
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    
    # بدء البوت
    updater.start_polling()
    logger.info("تم تشغيل البوت بنجاح")
    updater.idle()

if __name__ == '__main__':
    main()