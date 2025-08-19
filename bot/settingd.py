from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def settings_menu():
    keyboard = [
        [InlineKeyboardButton("🔑 ربط Binance", callback_data='link_binance')],
        [InlineKeyboardButton("💰 تعديل الرصيد", callback_data='edit_balance')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)
