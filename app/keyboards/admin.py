# app/keyboards/admin.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 لوحة التحكم")],
    ],
    resize_keyboard=True
)
