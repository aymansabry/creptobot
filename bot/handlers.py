from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import get_db, User

def create_menu():
    return ReplyKeyboardMarkup([["عرض الفرص"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        user = update.effective_user
        if not db.query(User).filter_by(telegram_id=user.id).first():
            db.add(User(telegram_id=user.id, first_name=user.first_name))
            db.commit()
        await update.message.reply_text("مرحبًا بك!", reply_markup=create_menu())
    finally:
        db.close()

def setup_handlers(app):
    app.add_handler(CommandHandler("start", start))
