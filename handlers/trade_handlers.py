from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from menus.main_menu import show_main_menu
from utils.logger import logger

async def show_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
        
        # محاكاة بيانات الفرص (ستستبدل بالوظيفة الفعلية)
        opportunities = [
            {"symbol": "BTC/USDT", "profit": "1.5%"},
            {"symbol": "ETH/USDT", "profit": "2.1%"}
        ]
        
        keyboard = [
            [InlineKeyboardButton(f"{opp['symbol']} - ربح {opp['profit']}", callback_data=f"opp_{idx}")]
            for idx, opp in enumerate(opportunities)
        ]
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
        
        await update.callback_query.edit_message_text(
            "📊 فرص المراجحة المتاحة:\n\n"
            "💡 اختر فرصة لبدء الاستثمار:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_opportunities: {str(e)}")
        await update.callback_query.edit_message_text("حدث خطأ أثناء جلب الفرص")

def setup_trade_handlers(application):
    application.add_handler(CallbackQueryHandler(show_opportunities, pattern="^show_opportunities$"))
