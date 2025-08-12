#main.py
import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from database import init_db, SessionLocal
from models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in environment variables.")

# تهيئة قاعدة البيانات
init_db()

# قائمة الأزرار
main_menu = [
    ["📈 عرض السوق", "💼 محفظتي"],
    ["⚙️ الإعدادات", "ℹ️ مساعدة"]
]

# تسجيل المستخدم
def register_user(telegram_id, username, first_name):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        db.add(user)
        db.commit()
        logger.info(f"✅ User registered: {telegram_id}")
    db.close()

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = update.effective_user
    register_user(user_data.id, user_data.username, user_data.first_name)
    await update.message.reply_text(
        f"أهلاً {user_data.first_name}! 👋\nاختر من القائمة:",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# التعامل مع الأزرار
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📈 عرض السوق":
        await update.message.reply_text("📊 جاري جلب بيانات السوق...")
        # استدعاء كود التحليل هنا
    elif text == "💼 محفظتي":
        await update.message.reply_text("📂 محفظتك فارغة حالياً.")
    elif text == "⚙️ الإعدادات":
        await update.message.reply_text("⚙️ الإعدادات قيد التطوير.")
    elif text == "ℹ️ مساعدة":
        await update.message.reply_text("ℹ️ بوت استثمار العملات الرقمية.")
    else:
        await update.message.reply_text("❓ لم أفهم الأمر.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
