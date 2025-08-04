from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters
from database import get_db_session, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📊 عرض الفرص", "💼 رصيدي"],
            ["⚙️ الإعدادات", "🆘 المساعدة"]
        ],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = get_db_session()
        user = update.effective_user
        
        if not session.query(User).filter_by(telegram_id=user.id).first():
            session.add(User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            ))
            session.commit()

        await update.message.reply_text(
            "مرحباً بك! اختر من القائمة:",
            reply_markup=create_main_menu()
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("حدث خطأ، يرجى المحاولة لاحقاً")
    finally:
        session.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📊 عرض الفرص":
        await update.message.reply_text("سيتم عرض الفرص هنا")
    elif text == "💼 رصيدي":
        await update.message.reply_text("سيتم عرض الرصيد هنا")

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
