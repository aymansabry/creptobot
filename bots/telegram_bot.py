import logging
from telegram.ext import Updater, CommandHandler
from core.exchanges import BinanceExchange  # الآن سيعمل بعد تعديل __init__.py
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
        "مرحباً! بوت المراجحة الآلي جاهز للعمل.\n"
        "أرسل /connect لربح حسابك"
    )

def connect_exchange(update, context):
    """معالجة ربط حساب التبادل"""
    try:
        # اختبار عمل BinanceExchange
        test_exchange = BinanceExchange("test_key", "test_secret")
        update.message.reply_text("تم تهيئة وحدة التبادل بنجاح!")
    except Exception as e:
        logger.error(f"Exchange init error: {e}")
        update.message.reply_text("حدث خطأ في تهيئة وحدة التبادل")

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    updater = Updater(Config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # تسجيل معالجات الأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("connect", connect_exchange))

    # بدء البوت
    updater.start_polling()
    logger.info("Bot started successfully")
    updater.idle()

if __name__ == '__main__':
    main()