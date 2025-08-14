from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)  # كل زر في صف منفصل
    kb.add(
        InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_edit_bot_profit"),
        InlineKeyboardButton("عدد المستخدمين الإجمالي", callback_data="admin_total_users"),
        InlineKeyboardButton("عدد المستخدمين أونلاين", callback_data="admin_online_users"),
        InlineKeyboardButton("تقارير الاستثمار", callback_data="admin_investment_reports"),
        InlineKeyboardButton("حالة البوت", callback_data="admin_bot_status"),
        InlineKeyboardButton("التداول كمستخدم عادي", callback_data="admin_trade_as_user")
    )
    return kb