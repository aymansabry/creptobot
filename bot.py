import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from handlers import router
import dotenv

dotenv.load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    logging.info("Starting DB migration...")
    import db_migration
    await db_migration.update_table_structure()
    logging.info("DB migration done. Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
