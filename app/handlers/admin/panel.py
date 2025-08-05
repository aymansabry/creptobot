# app/handlers/admin/panel.py
from aiogram import Router, F
from aiogram.types import Message
from app.database.utils import get_total_users, get_total_balance
from config.config import ADMIN_IDS

admin_router = Router()


@admin_router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ ليس لديك صلاحية الوصول.")

    total_users = await get_total_users()
    total_balance = await get_total_balance()

    text = (
        "<b>لوحة تحكم المدير</b>\n\n"
        f"👥 عدد المستخدمين: <b>{total_users}</b>\n"
        f"💰 إجمالي الأرصدة: <b>{total_balance:.2f} USDT</b>"
    )
    await message.answer(text)
