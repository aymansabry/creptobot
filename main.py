import os
import asyncio
from aiogram import Bot, Dispatcher
from config import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

async def main():
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 البوت يعمل على المنفذ {port}")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
