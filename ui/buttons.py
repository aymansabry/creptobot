from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def trade_confirmation_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تنفيذ الصفقة", callback_data="confirm_trade")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_trade")]
    ])
