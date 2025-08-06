from telegram import Update
from telegram.ext import ContextTypes
from core.config import config
import logging

logger = logging.getLogger(__name__)

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            f"رصيدك الحالي: 1000 USDT\n"
            f"الحد الأدنى للسحب: {config.MIN_INVESTMENT} USDT\n\n"
            "اختر العملية:\n"
            "1. إيداع\n"
            "2. سحب\n"
            "3. كشف حساب"
        )
    except Exception as e:
        logger.error(f"Error in wallet handler: {str(e)}")
        await update.message.reply_text("حدث خطأ في معالجة طلب المحفظة")
