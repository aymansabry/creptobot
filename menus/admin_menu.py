from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_edit_bot_profit"))
    kb.add(InlineKeyboardButton("عدد المستخدمين الإجمالي", callback_data="admin_total_users"))
    kb.add(InlineKeyboardButton("عدد المستخدمين أونلاين", callback_data="admin_online_users"))
    kb.add(InlineKeyboardButton("تقارير الاستثمار", callback_data="admin_investment_reports"))
    kb.add(InlineKeyboardButton("حالة البوت", callback_data="admin_bot_status"))
    kb.add(InlineKeyboardButton("التداول كمستخدم عادي", callback_data="admin_trade_as_user"))
    return kb