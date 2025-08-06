import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import config

# إعداد التسجيل (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# تهيئة البوت والتخزين
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

async def on_startup():
    """وظيفة تنفيذية عند بدء التشغيل"""
    logger.info("✅ البوت يعمل الآن!")
    if config.WEBHOOK_URL:
        await bot.set_webhook(
            f"{config.WEBHOOK_URL}/webhook",
            drop_pending_updates=True
        )

async def on_shutdown():
    """وظيفة تنفيذية عند إيقاف التشغيل"""
    logger.info("⛔ إيقاف البوت...")
    if config.WEBHOOK_URL:
        await bot.delete_webhook()
    await bot.session.close()

def create_app():
    """إنشاء تطبيق aiohttp للعمل مع Gunicorn"""
    from aiogram.webhook.aiohttp_server import (
        SimpleRequestHandler,
        setup_application
    )
    from aiohttp import web

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # تسجيل Webhook handler
    handler = SimpleRequestHandler(dp, bot)
    handler.register(app, path="/webhook")

    # إعداد تطبيق Aiogram
    setup_application(app, dp)

    return app

if __name__ == "__main__":
    import asyncio
    from aiogram import executor

    # وضع التشغيل (Webhook أو Polling)
    if config.WEBHOOK_URL:
        web.run_app(
            create_app(),
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000))
    else:
        logger.info("🚀 بدء التشغيل في وضع Polling...")
        executor.start_polling(
            dp,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
