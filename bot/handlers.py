from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import get_db, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_menu():
    """لوحة الأزرار الرئيسية"""
    return ReplyKeyboardMarkup([
        ["📊 فرص تداول", "💼 رصيدي"],
        ["⚙️ الإعدادات", "🆘 المساعدة"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = get_db()
        user = update.effective_user
        
        # تسجيل المستخدم إذا غير موجود
        if not db.query(User).filter_by(telegram_id=user.id).first():
            db.add(User(
                telegram_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name or ""
            ))
            db.commit()
        
        await update.message.reply_text(
            "مرحباً بك في بوت التداول الذكي!",
            reply_markup=create_menu()
        )
    except Exception as e:
        logger.error(f"خطأ في /start: {e}")
        await update.message.reply_text("حدث خطأ، يرجى المحاولة لاحقاً")
    finally:
        db.close()

def setup_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
