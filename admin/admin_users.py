from aiogram import Router, types
from aiogram.types import CallbackQuery
from database.crud import get_all_users

router = Router()

@router.callback_query(lambda c: c.data == "admin_users")
async def show_all_users(callback: CallbackQuery):
    users = await get_all_users()
    msg = f"👥 عدد العملاء: {len(users)}"
    await callback.message.edit_text(msg)
