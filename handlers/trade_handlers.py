from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils.logger import logger

async def show_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # محاكاة بيانات الفرص (يتم استبدالها بالوظيفة الفعلية لاحقاً)
        opportunities = [
            {"symbol": "BTC/USDT", "profit": "1.5%"},
            {"symbol": "ETH/USDT", "profit": "2.1%"}
        ]
        
        # إنشاء أزرار الفرص
        keyboard = [
            [InlineKeyboardButton(
                f"{opp['symbol']} - ربح {opp['profit']}", 
                callback_data=f"trade_{opp['symbol']}"
            )]
            for opp in opportunities
        ]
        
        # إضافة زر الرجوع
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
        
        # تحرير الرسالة الحالية لعرض الفرص
        await update.callback_query.edit_message_text(
            text="📊 فرص التداول المتاحة:\n\nاختر فرصة للاستثمار:",
            reply_markup=InlineKeyboardMarkup(keyboard)
            
    except Exception as e:
        logger.error(f"Error in show_opportunities: {str(e)}")
        await update.callback_query.edit_message_text("⚠️ حدث خطأ أثناء جلب الفرص")

async def handle_trade_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        symbol = query.data.replace("trade_", "")
        await query.edit_message_text(
            text=f"✅ اخترت تداول {symbol}\n\nأدخل المبلغ المراد استثماره (بالـ USDT):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("إلغاء", callback_data="cancel_trade")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in handle_trade_selection: {str(e)}")

def setup_trade_handlers(application):
    application.add_handler(CallbackQueryHandler(
        show_opportunities, 
        pattern="^show_opportunities$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_trade_selection,
        pattern="^trade_"
    ))
