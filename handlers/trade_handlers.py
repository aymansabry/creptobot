from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils.logger import logger

async def show_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # محاكاة بيانات الفرص
        opportunities = [
            {"symbol": "BTC/USDT", "profit": "1.5%"},
            {"symbol": "ETH/USDT", "profit": "2.1%"}
        ]
        
        keyboard = [
            [InlineKeyboardButton(f"{opp['symbol']} - ربح {opp['profit']}", 
             callback_data=f"trade_{opp['symbol']}")]
            for opp in opportunities
        ]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
        
        await update.callback_query.edit_message_text(
            "📊 فرص التداول المتاحة:",
            reply_markup=InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error showing opportunities: {str(e)}")

def setup_trade_handlers(application):
    application.add_handler(CallbackQueryHandler(show_opportunities, pattern="^show_opportunities$"))
