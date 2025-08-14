from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def user_main_menu_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("تسجيل أو تعديل بيانات التداول", callback_data="user_edit_exchange")],
            [InlineKeyboardButton("ابدأ استثمار", callback_data="user_start_investment")],
            [InlineKeyboardButton("استثمار وهمي", callback_data="user_demo_investment")],
            [InlineKeyboardButton("كشف حساب عن فترة", callback_data="user_account_statement")],
            [InlineKeyboardButton("حالة السوق", callback_data="user_market_status")],
            [InlineKeyboardButton("إيقاف الاستثمار", callback_data="user_stop_investment")]
        ]
    )
    return kb