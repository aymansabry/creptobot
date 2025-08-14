from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def user_main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("إدارة بيانات التداول", callback_data="user_manage"))
    kb.add(InlineKeyboardButton("ابدأ الاستثمار", callback_data="user_start"))
    kb.add(InlineKeyboardButton("استثمار وهمي", callback_data="user_demo"))
    kb.add(InlineKeyboardButton("كشف حساب", callback_data="user_statement"))
    kb.add(InlineKeyboardButton("إيقاف الاستثمار", callback_data="user_stop"))
    kb.add(InlineKeyboardButton("حالة السوق", callback_data="market_status"))
    return kb