from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import logging
from config import Config

# إعداد نظام التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [
            [InlineKeyboardButton("🔄 ربط الحسابات", callback_data="connect")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")]
        ]
        await update.message.reply_text(
            "مرحباً! اختر من القائمة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error in start: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()  # ضروري لإيقاف أيقونة التحميل
        
        if query.data == "connect":
            keyboard = [
                [InlineKeyboardButton("بينانس", callback_data="binance")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ]
            await query.edit_message_text(
                text="اختر المنصة:",
                reply_markup=InlineKeyboardMarkup(keyboard))
                
        elif query.data == "back":
            keyboard = [
                [InlineKeyboardButton("🔄 ربط الحسابات", callback_data="connect")],
                [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")]
            ]
            await query.edit_message_text(
                text="القائمة الرئيسية:",
                reply_markup=InlineKeyboardMarkup(keyboard))
                
        elif query.data == "binance":
            await query.edit_message_text(
                text="جاري إعداد اتصال ببينانس...")
            
        elif query.data == "stats":
            await query.edit_message_text(
                text="جاري تحميل الإحصائيات...")
                
    except Exception as e:
        logger.error(f"Error in button handler: {e}")

def main():
    try:
        # إيقاف أي نسخ سابقة
        app = Application.builder().token(Config.BOT_TOKEN).build()
        
        # إضافة المعالجات
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        
        # تشغيل البوت
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()