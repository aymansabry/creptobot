from telegram import ReplyKeyboardMarkup
from core.config import config
from db.postgres import Database
import logging

logger = logging.getLogger(__name__)

async def show_main_menu(update):
    try:
        user_id = update.effective_user.id
        with Database.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
                balance = cur.fetchone()[0] if cur.rowcount > 0 else 0.0

        menu_options = [
            ["💰 استثمار جديد", "📊 تحليل السوق"],
            ["💼 محفظتي", "📋 الصفقات النشطة"],
            ["⚙️ الإعدادات", "🆘 الدعم الفني"]
        ]
        
        await update.message.reply_text(
            f"مرحبًا {update.effective_user.first_name}!\n"
            f"رصيدك الحالي: {balance:.2f} USDT\n"
            f"الحد الأدنى للاستثمار: {config.MIN_INVESTMENT} USDT\n\n"
            "اختر من القائمة:",
            reply_markup=ReplyKeyboardMarkup(menu_options, resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Error in show_main_menu: {str(e)}")
        await update.message.reply_text("حدث خطأ في تحميل القائمة الرئيسية")
