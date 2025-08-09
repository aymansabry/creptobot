from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db.session import get_session
from db.models import User

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username

    session = get_session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        session.commit()

    await update.message.reply_text(f"مرحباً {username or 'صديقي'}! تم تسجيلك في النظام.")

start_handler = CommandHandler("start", start)
