from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from database import get_db_session, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء قائمة الأزرار الرئيسية
def create_main_menu():
    return ReplyKeyboardMarkup(
        [
            ["📊 عرض الفرص", "💼 رصيدي"],
            ["⚙️ الإعدادات", "🆘 المساعدة"]
        ],
        resize_keyboard=True,
        input_field_placeholder="اختر من القائمة"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        session = get_db_session()
        
        # تسجيل المستخدم الجديد
        if not session.query(User).filter_by(telegram_id=user.id).first():
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(new_user)
            session.commit()
        
        # إرسال رسالة الترحيب مع القائمة
        await update.message.reply_text(
            "مرحباً بك في بوت التداول الذكي!",
            reply_markup=create_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text(
            "حدث خطأ تقني، يرجى المحاولة لاحقاً",
            reply_markup=create_main_menu()
        )
    finally:
        session.close()

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        if text == "📊 عرض الفرص":
            await show_opportunities(update, context)
        elif text == "💼 رصيدي":
            await show_balance(update, context)
        elif text == "⚙️ الإعدادات":
            await show_settings(update, context)
        elif text == "🆘 المساعدة":
            await show_help(update, context)
    except Exception as e:
        logger.error(f"Menu error: {e}")
        await update.message.reply_text(
            "حدث خطأ في معالجة طلبك",
            reply_markup=create_main_menu()
        )

def setup_handlers(application):
    # handler للبدء
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_selection))
    application.add_handler(CommandHandler("start", start))
