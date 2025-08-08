from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
from ui.menus import user_main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك في البوت!", reply_markup=user_main_menu())

def user_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
