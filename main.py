#main.py
import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# =========================
# إعدادات اللوج
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# قراءة التوكن من متغير البيئة
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود! تأكد من وضعه في متغيرات البيئة.")

# =========================
# أوامر البوت
# =========================
async def start(update, context):
    await update.message.reply_text("🚀 البوت شغال تمام! أهلاً بيك 🌟")

async def echo(update, context):
    await update.message.reply_text(f"📩 إنت كتبت: {update.message.text}")

# =========================
# تشغيل البوت
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # أمر /start
    app.add_handler(CommandHandler("start", start))

    # الرد على أي رسالة نصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("🚀 البوت بدأ ويعمل في وضع polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
