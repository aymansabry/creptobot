from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import Config
import logging

# إعداد نظام التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [
            [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')]
        ]
        # إذا كانت الرسالة من /start مباشرة
        if update.message:
            await update.message.reply_text(
                "القائمة الرئيسية:",
                reply_markup=InlineKeyboardMarkup(keyboard)
        # إذا كانت من زر رجوع
        else:
            await update.callback_query.edit_message_text(
                "القائمة الرئيسية:",
                reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error in start: {e}")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'connect':
            keyboard = [
                [InlineKeyboardButton("بينانس", callback_data='binance')],
                [InlineKeyboardButton("🔙 رجوع", callback_data='back')]
            ]
            await query.edit_message_text(
                text="اختر المنصة:",
                reply_markup=InlineKeyboardMarkup(keyboard))
                
        elif query.data == 'back':
            # استدعاء واجهة القائمة الرئيسية مع تعديل الرسالة الحالية
            keyboard = [
                [InlineKeyboardButton("🔄 ربط الحسابات", callback_data='connect')],
                [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')]
            ]
            await query.edit_message_text(
                text="القائمة الرئيسية:",
                reply_markup=InlineKeyboardMarkup(keyboard))
                
    except Exception as e:
        logger.error(f"Error in handle_buttons: {e}")

def main():
    try:
        app = Application.builder().token(Config.BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(handle_buttons))
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == '__main__':
    main()