import asyncio
import logging
import os
from telegram.ext import ApplicationBuilder
from database import init_db
from handlers import setup_handlers

# إعداد تسجيل الأحداث
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ لم يتم ضبط متغير TELEGRAM_BOT_TOKEN في البيئة.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    await init_db()
    setup_handlers(app)
    logger.info("✅ البوت يعمل الآن...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
