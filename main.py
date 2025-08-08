import logging
import asyncio
import nest_asyncio
from telegram.ext import Application
from core.config import TELEGRAM_BOT_TOKEN
from database.base import init_db
from handlers import setup_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # تهيئة قاعدة البيانات
    await init_db()
    print("\n✅ تم تهيئة قاعدة البيانات")

    # إعداد البوت
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # إعداد الـ Handlers
    setup_handlers(app)
    print("\n✅ تم إعداد الـ Handlers")

    logger.info("✅ البوت يعمل الآن...")
    await app.run_polling()


if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise
