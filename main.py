import asyncio
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application

from core.logger import setup_logger
from handlers.user import user_handlers
from handlers.admin import admin_handlers
from handlers.common import common_handlers

# تحميل متغيرات البيئة من .env
load_dotenv()

# إعداد السجل
setup_logger()
logger = logging.getLogger(__name__)


async def main():
    # تحميل التوكن من البيئة
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN غير موجود في متغيرات البيئة.")
        return

    # بناء التطبيق
    app = Application.builder().token(token).build()

    # تسجيل الهاندلرز
    user_handlers(app)
    admin_handlers(app)
    common_handlers(app)

    logger.info("✅ البوت يعمل الآن...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
