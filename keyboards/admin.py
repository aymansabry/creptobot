from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👥 عدد العملاء", callback_data="admin_users")],
    [InlineKeyboardButton(text="📈 الربح الإجمالي", callback_data="admin_profit")],
    [InlineKeyboardButton(text="⚙️ إعدادات الاستثمار", callback_data="admin_settings")],
])
