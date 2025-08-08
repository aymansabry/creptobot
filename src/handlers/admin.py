from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
from ui.menus import admin_main_menu

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لوحة التحكم", reply_markup=admin_main_menu())

def admin_handlers(app: Application):
    app.add_handler(CommandHandler("admin", admin))
