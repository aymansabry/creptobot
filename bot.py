import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from db import get_user_by_telegram_id, get_all_live_users
from arbitrage import arbitrage_loop_all_users
from security import decrypt_api_key
import logging
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_bot(message: types.Message):
    await message.answer("أهلاً بك في بوت المراجحة التلقائية! الرجاء الانتظار...")

async def on_startup():
    logging.info("Starting arbitrage loop")
    asyncio.create_task(arbitrage_loop_all_users(bot))

async def main():
    await dp.start_polling()

if __name__ == "__main__":
    import dotenv, logging
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
