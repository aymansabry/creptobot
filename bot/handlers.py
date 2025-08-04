from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import get_db_session, User  # Direct imports
from config import Config
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = get_db_session()
        user = update.effective_user
        
        # User registration logic
        if not session.query(User).filter_by(telegram_id=user.id).first():
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(new_user)
            session.commit()
        
        keyboard = ReplyKeyboardMarkup([["📊 عرض الفرص"]], resize_keyboard=True)
        await update.message.reply_text("مرحباً بك! اختر 'عرض الفرص' للبدء", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text("حدث خطأ، يرجى المحاولة لاحقاً")
    finally:
        session.close()

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
