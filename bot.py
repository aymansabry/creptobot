import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from db import init_db
from handlers import register_handlers

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    if not BOT_TOKEN:
        raise ValueError("❌ متغير TELEGRAM_BOT_TOKEN غير موجود في .env")

    # إنشاء البوت والمخزن
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    # تهيئة قاعدة البيانات (إنشاء الجداول لو مش موجودة)
    init_db()

    # تسجيل جميع الهاندلرز
    register_handlers(dp)

    print("✅ البوت يعمل الآن...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
