import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from menus.admin_menu import admin_main_menu_keyboard
from menus.user_menu import user_main_menu_keyboard
from arbitrage.run_arbitrage import run_arbitrage_for_all_users

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------- Start command ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("مرحبًا بالمدير! اختر عملية:", reply_markup=admin_main_menu_keyboard())
    else:
        await message.answer("مرحبًا! اختر عملية:", reply_markup=user_main_menu_keyboard())

# ---------- Callback handler ----------
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    await call.answer("تم الضغط ✅")  # أي رد أولي
    # يمكن استدعاء دوال القوائم هنا حسب call.data

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))