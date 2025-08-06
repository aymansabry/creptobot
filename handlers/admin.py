from aiogram import types, Router
from aiogram.types import CallbackQuery
from keyboards.admin import admin_panel
from database.stats import get_total_users, get_total_profit

router = Router()

@router.message(commands=["admin"])
async def admin_panel_handler(message: types.Message):
    await message.answer("👑 لوحة المدير:", reply_markup=admin_panel)

@router.callback_query(lambda c: c.data == "admin_users")
async def admin_users_count(callback: CallbackQuery):
    count = await get_total_users()
    await callback.message.edit_text(f"👥 عدد العملاء المسجلين: {count}")

@router.callback_query(lambda c: c.data == "admin_profit")
async def admin_total_profit(callback: CallbackQuery):
    total = await get_total_profit()
    await callback.message.edit_text(f"💰 الربح الإجمالي: {total:.2f} USDT")

@router.callback_query(lambda c: c.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    await callback.message.edit_text("⚙️ إعدادات الاستثمار سيتم إضافتها لاحقاً.")
