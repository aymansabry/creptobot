from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 مرحباً بك في بوت تداول العملات الرقمية بالذكاء الاصطناعي.")

def setup_user_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))