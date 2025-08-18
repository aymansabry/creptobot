import logging
from telegram.ext import Updater, CommandHandler
from core.exchanges.binance import BinanceExchange
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text("مرحباً! بوت المراجحة يعمل الآن بنجاح")

def main():
    # اختبار وحدة التبادل
    try:
        exchange = BinanceExchange("test", "test")
        logger.info("تم تهيئة BinanceExchange بنجاح")
    except Exception as e:
        logger.error(f"خطأ في تهيئة BinanceExchange: {e}")

    # إنشاء Updater بدون use_context
    updater = Updater(Config.BOT_TOKEN)
    
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    
    updater.start_polling()
    logger.info("تم تشغيل البوت بنجاح")
    updater.idle()

if __name__ == '__main__':
    main()