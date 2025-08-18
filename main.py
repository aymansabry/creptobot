from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from config import Config
import logging

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض إعدادات البوت الحالية"""
    await update.message.reply_text(Config.show_settings())

def setup_bot():
    """تهيئة وتشغيل البوت"""
    try:
        app = Application.builder().token(Config.BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        
        logging.info("جارٍ تشغيل البوت...")
        app.run_polling()
    except Exception as e:
        logging.error(f"خطأ في تشغيل البوت: {e}")
        exit(1)

if __name__ == "__main__":
    setup_bot()