from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل /start للبدء")

def common_handlers(app: Application):
    app.add_handler(CommandHandler("help", help_command))
