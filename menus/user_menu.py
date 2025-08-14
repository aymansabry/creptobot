from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def user_main_menu_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("إدارة بيانات التداول", callback_data="user_manage_trading"))
    kb.add(InlineKeyboardButton("ابدأ الاستثمار", callback_data="user_start_investment"))
    kb.add(InlineKeyboardButton("استثمار وهمي", callback_data="user_demo_investment"))
    kb.add(InlineKeyboardButton("كشف حساب", callback_data="user_account_statement"))
    kb.add(InlineKeyboardButton("إيقاف الاستثمار", callback_data="user_stop_investment"))
    kb.add(InlineKeyboardButton("حالة السوق", callback_data="market_status"))
    return kb