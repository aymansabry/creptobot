import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers.user_handlers import register_user_handlers
from handlers.admin_handlers import register_admin_handlers
from database.core import create_tables

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="/start", description="ابدأ"),
        BotCommand(command="/admin", description="لوحة المدير")
    ])

async def main():
    await create_tables()
    register_user_handlers(dp)
    register_admin_handlers(dp)
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
