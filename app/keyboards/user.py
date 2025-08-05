# app/keyboards/user.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

user_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💸 استثمار")],
        [KeyboardButton(text="📊 محفظتي")],
        [KeyboardButton(text="ℹ️ معلومات")],
    ],
    resize_keyboard=True
)
