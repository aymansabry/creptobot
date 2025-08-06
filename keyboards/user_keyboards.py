from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💼 فرص استثمارية", callback_data="show_deals"),
        InlineKeyboardButton("📊 محفظتي", callback_data="my_wallet"),
        InlineKeyboardButton("💸 تحويل أرباحي", callback_data="withdraw"),
        InlineKeyboardButton("🧠 استثمار تلقائي", callback_data="auto_invest"),
    )
    return keyboard
