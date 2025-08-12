import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler
from telegram.error import Conflict
import requests

# الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# ======= حذف أي Webhook موجود قبل البدء =======
def delete_existing_webhook():
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        r = requests.post(url, timeout=10)
        if r.status_code == 200:
            logger.info("✅ Webhook deleted successfully.")
        else:
            logger.warning(f"⚠️ Failed to delete webhook: {r.text}")
    except Exception as e:
        logger.error(f"❌ Error deleting webhook: {e}")


# ======= الأوامر =======
async def start(update, context):
    await update.message.reply_text("مرحبًا! البوت شغال تمام ✅")


# ======= التشغيل =======
async def main():
    delete_existing_webhook()  # حذف الـ Webhook قبل التشغيل

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    try:
        logger.info("🚀 Bot is starting in polling mode...")
        await app.run_polling()
    except Conflict:
        logger.error("❌ Conflict detected: Bot is already running elsewhere.")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
