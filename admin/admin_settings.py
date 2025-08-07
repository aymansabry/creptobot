from aiogram import Router, types
from aiogram.types import CallbackQuery
from database.crud import get_settings, update_settings

router = Router()

@router.callback_query(lambda c: c.data == "admin_settings")
async def show_settings(callback: CallbackQuery):
    settings = await get_settings()
    msg = (
        "⚙️ الإعدادات الحالية:\n\n"
        f"💵 الحد الأدنى: {settings.min_amount} USDT\n"
        f"💰 الحد الأقصى: {settings.max_amount} USDT\n"
        f"📉 نسبة ربح البوت: {settings.bot_percentage}%"
    )
    await callback.message.edit_text(msg)
