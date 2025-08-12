import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from database import init_db, SessionLocal, User

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN مش موجود في .env")

# تشغيل اللوج
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات
init_db()

async def start(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username

    db = SessionLocal()
    if not db.query(User).filter_by(telegram_id=user_id).first():
        new_user = User(telegram_id=user_id, username=username)
        db.add(new_user)
        db.commit()
        logger.info(f"تم تسجيل مستخدم جديد: {username}")
    db.close()

    await update.message.reply_text("أهلاً! تم تسجيلك في النظام ✅")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    logger.info("🚀 البوت شغال...")
    app.run_polling()
