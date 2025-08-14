from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="تعديل نسبة ربح البوت", callback_data="admin_edit_bot_profit")],
            [InlineKeyboardButton(text="عدد المستخدمين الإجمالي", callback_data="admin_total_users")],
            [InlineKeyboardButton(text="عدد المستخدمين أونلاين", callback_data="admin_online_users")],
            [InlineKeyboardButton(text="تقارير الاستثمار", callback_data="admin_investment_reports")],
            [InlineKeyboardButton(text="حالة البوت", callback_data="admin_bot_status")],
            [InlineKeyboardButton(text="التداول كمستخدم عادي", callback_data="admin_trade_as_user")]
        ]
    )
    return kb