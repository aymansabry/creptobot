from telegram import ReplyKeyboardMarkup
from core.config import Config

def wallet_menu(update):
    buttons = [
        ["💰 إيداع", "🚀 سحب"],
        ["📊 كشف الحساب", "↩ رجوع"]
    ]
    update.message.reply_text(
        f"رصيدك الحالي: {get_user_balance(update.effective_user.id)} {Config.CURRENCY}",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
