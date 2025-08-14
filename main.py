import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from db.db_setup import init_db, SessionLocal, User
from menus.user_menu import user_main_menu_keyboard
from menus.admin_menu import admin_main_menu_keyboard
from arbitrage.run_arbitrage import run_arbitrage_for_all_users
from config import BOT_TOKEN, ADMIN_ID

init_db()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("مرحبًا بالمدير! اختر عملية:", reply_markup=admin_main_menu_keyboard())
    else:
        await message.answer("مرحبًا! اختر عملية:", reply_markup=user_main_menu_keyboard())

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))