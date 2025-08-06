from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery
from keyboards.admin_keyboards import admin_panel
from database.admin import get_total_users, get_total_profit

async def admin_command(message: types.Message):
    if message.from_user.id != 123456789:  # ضع ID المدير هنا
        return
    await message.answer("🛠️ لوحة تحكم المدير", reply_markup=admin_panel())

async def total_users_callback(call: CallbackQuery):
    count = await get_total_users()
    await call.message.answer(f"👥 عدد المستخدمين: {count}")

async def total_profit_callback(call: CallbackQuery):
    profit = await get_total_profit()
    await call.message.answer(f"💰 إجمالي الأرباح: {profit:.2f} USDT")

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_command, commands=["admin"])
    dp.register_callback_query_handler(total_users_callback, text="admin_users")
    dp.register_callback_query_handler(total_profit_callback, text="admin_profits")
