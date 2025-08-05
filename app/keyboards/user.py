# app/keyboards/user.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

user_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 الاستثمار")],
        [KeyboardButton(text="📊 محفظتي"), KeyboardButton(text="💸 سحب الأرباح")],
        [KeyboardButton(text="⚙️ الإعدادات")]
    ],
    resize_keyboard=True
)
