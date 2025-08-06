import os
from aiogram import Bot, Dispatcher
from aiogram.dispatcher import Dispatcher
from config import config

async def on_startup():
    print("✅ البوت يعمل الآن!")

def create_dispatcher():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()  # لا تمرر البوت هنا
    dp.startup.register(on_startup)
    return dp

dp = create_dispatcher()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
