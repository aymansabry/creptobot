from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import get_db, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        user = update.effective_user
        
        # التحقق من وجود المستخدم أولاً
        existing_user = db.query(User).filter_by(telegram_id=user.id).first()
        if not existing_user:
            new_user = User(
                telegram_id=user.id,
                first_name=user.first_name[:50]  # تأكد من عدم تجاوز الحد الأقصى
            )
            db.add(new_user)
            db.commit()
            logger.info(f"تم تسجيل مستخدم جديد: {user.id}")
        
        await update.message.reply_text("مرحباً بك في البوت!")
        
    except Exception as e:
        logger.error(f"خطأ في التسجيل: {e}")
        db.rollback()
        await update.message.reply_text("حدث خطأ تقني، يرجى المحاولة لاحقاً")
    finally:
        db.close()

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
