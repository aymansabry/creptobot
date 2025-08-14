from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def user_main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)  # كل زر في صف منفصل
    kb.add(
        InlineKeyboardButton("إدارة بيانات التداول", callback_data="user_manage_trading"),
        InlineKeyboardButton("ابدأ الاستثمار", callback_data="user_start_investment"),
        InlineKeyboardButton("استثمار وهمي", callback_data="user_demo_investment"),
        InlineKeyboardButton("كشف حساب", callback_data="user_account_statement"),
        InlineKeyboardButton("إيقاف الاستثمار", callback_data="user_stop_investment"),
        InlineKeyboardButton("حالة السوق", callback_data="market_status")
    )
    return kb