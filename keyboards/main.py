from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 استثمار جديد", callback_data="new_investment")],
    [InlineKeyboardButton(text="📊 حالة استثماراتي", callback_data="my_investments")],
    [InlineKeyboardButton(text="🧠 تحليل الصفقات", callback_data="analyze_trades")],
    [InlineKeyboardButton(text="📞 الدعم الفني", callback_data="support")],
])
