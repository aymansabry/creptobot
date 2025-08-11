import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from handlers import router  # تأكد إن handlers.py في نفس المجلد أو مسار صحيح
import dotenv

dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
