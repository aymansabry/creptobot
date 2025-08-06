from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👤 عدد المستخدمين", callback_data="admin_users"),
        InlineKeyboardButton("💰 اجمالي الارباح", callback_data="admin_profits"),
        InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="admin_settings"),
        InlineKeyboardButton("📬 رسائل للعملاء", callback_data="admin_broadcast"),
    )
    return keyboard
