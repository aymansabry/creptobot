from telegram import Update
from telegram.ext import ContextTypes
from core.config import config
import logging

logger = logging.getLogger(__name__)

async def analyze_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # هنا سيتم استدعاء الذكاء الاصطناعي لتحليل السوق
        analysis_result = "تحليل السوق:\n- فرصة شراء BTC/USDT\n- سعر مستهدف: +2.5%\n- ثقة: 85%"
        
        await update.message.reply_text(
            f"📊 نتائج التحليل:\n\n{analysis_result}\n\n"
            f"الحد الأدنى للاستثمار: {config.MIN_INVESTMENT} USDT"
        )
    except Exception as e:
        logger.error(f"Error in analyze_market: {str(e)}")
        await update.message.reply_text("حدث خطأ أثناء تحليل السوق")

async def handle_investment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # معالجة اختيارات المستخدم
    if query.data.startswith("invest_"):
        amount = float(query.data.split("_")[1])
        await query.edit_message_text(f"تم استلام طلب استثمار بقيمة {amount} USDT")
