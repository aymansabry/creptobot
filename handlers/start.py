from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💼 محفظتي", "📊 الرصيد"],
        ["🤖 بدء التداول", "👤 حسابي"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 مرحبًا بك في بوت التداول الآلي.\nاختر من القائمة:", reply_markup=reply_markup)

start_handler = CommandHandler("start", start)
