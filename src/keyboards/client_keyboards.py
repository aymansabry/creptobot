from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 استثمار تلقائي"), KeyboardButton(text="📈 صفقات اليوم")],
        [KeyboardButton(text="💼 محفظتي"), KeyboardButton(text="📞 الدعم الفني")]
    ],
    resize_keyboard=True
)
