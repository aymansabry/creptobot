import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import router  # استيراد الراوتر من ملف handlers.py

API_TOKEN = "توكن_البوت_خاصتك_هنا"

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)  # تسجيل الراوتر في الديسباتشر
    await dp.start_polling(bot)  # بدء البولينج مع ربط البوت

if __name__ == "__main__":
    asyncio.run(main())
