from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config

router = Router(name="admin")

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in config.ADMINS:
        return await message.answer("❌ ليس لديك صلاحية الدخول هنا")
    
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="إحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton(text="إدارة الصفقات", callback_data="admin_deals"),
        types.InlineKeyboardButton(text="إرسال إشعار", callback_data="admin_notify")
    )
    builder.adjust(1)
    
    await message.answer(
        "👨‍💻 لوحة التحكم الإدارية",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer("📊 الإحصائيات:\n\n- عدد المستخدمين: 150\n- الصفقات النشطة: 12")

__all__ = ['router']
