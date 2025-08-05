# app/keyboards/admin.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📈 إحصائيات البوت"), KeyboardButton(text="🧮 ضبط النسبة")],
        [KeyboardButton(text="👥 العملاء"), KeyboardButton(text="💼 صفقات نشطة")],
        [KeyboardButton(text="📨 تذاكر الدعم")]
    ],
    resize_keyboard=True
)
