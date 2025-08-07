from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 عرض الصفقات", callback_data="view_deals")],
        [InlineKeyboardButton(text="💸 الاستثمار الآن", callback_data="start_invest")],
        [InlineKeyboardButton(text="🧾 حالة الاستثمار", callback_data="my_investments")],
        [InlineKeyboardButton(text="📞 الدعم الفني", callback_data="contact_support")]
    ])
