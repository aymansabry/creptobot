# bot.py
import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import inspect
from database import init_db, engine
from handlers import router
from trading import start_background_tasks

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

if not TELEGRAM_BOT_TOKEN:
    logger.error("Missing TELEGRAM_BOT_TOKEN in environment.")
    raise SystemExit("Set TELEGRAM_BOT_TOKEN in env")

def init_db_once():
    """إنشاء الجداول أول مرة فقط إذا غير موجودة"""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        logger.info("Creating database tables for the first time...")
        init_db()
    else:
        logger.info("Database tables already exist. Skipping creation.")

async def main():
    # 1) إنشاء الجداول إذا غير موجودة
    init_db_once()

    # 2) بوت ودي سباتشر
    bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # 3) ابدأ الخلفيات (مراجحة + تحديث رصيد دوري)
    start_background_tasks(bot)

    logger.info("Bot starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
