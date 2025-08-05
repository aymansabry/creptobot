# app/keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

confirm_investment_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأكيد الاستثمار", callback_data="confirm_investment")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_investment")]
    ]
)

admin_profit_adjust_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ زيادة النسبة", callback_data="increase_profit")],
        [InlineKeyboardButton(text="⬇️ تقليل النسبة", callback_data="decrease_profit")]
    ]
)
