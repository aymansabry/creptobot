from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from buttons import get_review_buttons

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في بوت المراجعة الثلاثية! استخدم /review للبدء.")

async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = get_review_buttons()
    await update.message.reply_text("اختر نوع المراجعة:", reply_markup=InlineKeyboardMarkup(buttons))