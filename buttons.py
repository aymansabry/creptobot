from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

def get_review_buttons():
    return [
        [InlineKeyboardButton("🔍 مراجعة منتج", callback_data="product")],
        [InlineKeyboardButton("📍 مراجعة مكان", callback_data="place")],
        [InlineKeyboardButton("🎬 مراجعة فيلم", callback_data="movie")]
    ]

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    response = {
        "product": "🛍 أرسل اسم المنتج الذي تريد مراجعته.",
        "place": "📍 أرسل اسم المكان الذي تريد مراجعته.",
        "movie": "🎬 أرسل اسم الفيلم الذي تريد مراجعته."
    }.get(choice, "❓ اختيار غير معروف.")

    await query.edit_message_text(response)