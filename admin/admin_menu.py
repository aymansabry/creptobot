from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import ADMIN_IDS

router = Router()

@router.message()
async def admin_entry(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 العملاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="admin_settings")],
        [InlineKeyboardButton(text="💼 الصفقات الجارية", callback_data="admin_trades")],
        [InlineKeyboardButton(text="🧑‍💼 الدعم الفني", callback_data="admin_support")],
    ])
    await message.answer("🛠 لوحة تحكم المدير:", reply_markup=kb)
