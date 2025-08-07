from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from utils.logger import logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [
            [InlineKeyboardButton("💰 فرص استثمارية", callback_data="show_opportunities")],
            [InlineKeyboardButton("💼 محفظتي", callback_data="show_wallet")],
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")]
        ]
        
        await update.message.reply_text(
            "مرحباً بك في بوت التداول الآلي!\nاختر أحد الخيارات:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "show_opportunities":
            await show_opportunities(update, context)
        elif query.data == "show_wallet":
            await show_wallet(update, context)
        elif query.data == "settings":
            await show_settings(update, context)
            
    except Exception as e:
        logger.error(f"Error in button handler: {str(e)}")

async def show_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # سيتم تنفيذها في trade_handlers
    pass

async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # كود عرض المحفظة هنا
        pass
    except Exception as e:
        logger.error(f"Error showing wallet: {str(e)}")

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
