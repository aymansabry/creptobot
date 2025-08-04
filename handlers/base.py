from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from core.database import db
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    def __init__(self):
        self.session = db.get_session()
        
    async def safe_execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, func):
        try:
            await func(update, context)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            await update.message.reply_text("حدث خطأ في النظام، يرجى المحاولة لاحقاً")
        finally:
            self.session.close()

def create_menu():
    return ReplyKeyboardMarkup([
        ["📊 الفرص", "💼 الرصيد"],
        ["⚙️ الإعدادات", "🆘 المساعدة"]
    ], resize_keyboard=True)
