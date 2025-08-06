from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import config

async def show_new_investment(update, context):
    try:
        amounts = [
            [InlineKeyboardButton("10 USDT", callback_data="invest_10")],
            [InlineKeyboardButton("50 USDT", callback_data="invest_50")],
            [InlineKeyboardButton("100 USDT", callback_data="invest_100")]
        ]
        
        await update.message.reply_text(
            "اختر مبلغ الاستثمار:",
            reply_markup=InlineKeyboardMarkup(amounts)
        )
    except Exception as e:
        await update.message.reply_text("حدث خطأ في عرض خيارات الاستثمار")
