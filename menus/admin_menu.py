from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("تعديل نسبة ربح البوت", callback_data="admin_edit_bot_profit")],
            [InlineKeyboardButton("عدد المستخدمين اجمالي", callback_data="admin_total_users")],
            [InlineKeyboardButton("عدد المستخدمين اونلاين", callback_data="admin_online_users")],
            [InlineKeyboardButton("تقارير الاستثمار اجمالا عن فترة", callback_data="admin_investment_report")],
            [InlineKeyboardButton("حالة البوت برمجيا", callback_data="admin_bot_status")],
            [InlineKeyboardButton("التداول كمستخدم عادي", callback_data="admin_trade_as_user")]
        ]
    )
    return kb