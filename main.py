#main.py
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import init_db, SessionLocal
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# إعداد اللوجات
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات
init_db(DATABASE_URL)

# دوال أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📊 تحليل السوق", "💰 بدء استثمار"],
        ["⚙️ الإعدادات", "ℹ️ المساعدة"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("مرحباً بك في البوت! اختر من القائمة:", reply_markup=reply_markup)

async def market_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري تحليل السوق...")

async def start_investment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ تم بدء الاستثمار!")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ هنا الإعدادات.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ هذه هي قائمة المساعدة.")

# إنشاء التطبيق
def main():
    application = Application.builder().token(TOKEN).build()

    # أوامر
    application.add_handler(CommandHandler("start", start))

    # رسائل نصية
    application.add_handler(MessageHandler(filters.Text("📊 تحليل السوق"), market_analysis))
    application.add_handler(MessageHandler(filters.Text("💰 بدء استثمار"), start_investment))
    application.add_handler(MessageHandler(filters.Text("⚙️ الإعدادات"), settings))
    application.add_handler(MessageHandler(filters.Text("ℹ️ المساعدة"), help_command))

    logger.info("🚀 البوت بدأ ويعمل في وضع polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
