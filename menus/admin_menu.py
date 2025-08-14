from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_profit"))
    kb.add(InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users"))
    kb.add(InlineKeyboardButton("عدد المستخدمين أونلاين", callback_data="admin_online"))
    kb.add(InlineKeyboardButton("تقارير الاستثمار", callback_data="admin_reports"))
    kb.add(InlineKeyboardButton("حالة البوت", callback_data="admin_status"))
    kb.add(InlineKeyboardButton("التداول كمستخدم عادي", callback_data="admin_trade_as_user"))
    return kb