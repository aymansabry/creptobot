#main.py
import os
import subprocess
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود! تأكد من وضعه في متغيرات البيئة.")

def run_migrations():
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("✅ المايجريشن تم بنجاح.")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل المايجريشن: {e}")

async def start(update, context):
    await update.message.reply_text("🚀 البوت شغال تمام! أهلاً بيك 🌟")

async def echo(update, context):
    await update.message.reply_text(f"📩 إنت كتبت: {update.message.text}")

def main():
    run_migrations()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("🚀 البوت بدأ ويعمل في وضع polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
