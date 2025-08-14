from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def user_main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="إدارة بيانات التداول", callback_data="user_manage_trading")],
            [InlineKeyboardButton(text="ابدأ الاستثمار", callback_data="user_start_investment")],
            [InlineKeyboardButton(text="استثمار وهمي", callback_data="user_demo_investment")],
            [InlineKeyboardButton(text="كشف حساب", callback_data="user_account_statement")],
            [InlineKeyboardButton(text="إيقاف الاستثمار", callback_data="user_stop_investment")],
            [InlineKeyboardButton(text="حالة السوق", callback_data="market_status")]
        ]
    )
    return kb

def amount_input_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="الرجوع", callback_data="back_to_trading_setup")]
        ]
    )
    return kb