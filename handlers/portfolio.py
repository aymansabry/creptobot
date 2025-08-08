from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 محفظتك حالياً فارغة.")

portfolio_handler = CommandHandler("portfolio", portfolio)