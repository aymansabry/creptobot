from aiogram import Router, types
from aiogram.filters import Command
from config.config import ADMIN_IDS

admin_router = Router()

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ لا تملك صلاحية الوصول.")
    await message.answer("✅ مرحباً بك في لوحة الإدارة.")
