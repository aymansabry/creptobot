from telegram import Update
from telegram.ext import ContextTypes
from core.config import config
import logging

logger = logging.getLogger(__name__)

async def handle_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            f"أدخل مبلغ الاستثمار (الحد الأدنى {config.MIN_INVESTMENT} USDT):\n\n"
            "أو اختر من الخيارات السريعة:\n"
            "1. 10 USDT\n"
            "2. 50 USDT\n"
            "3. 100 USDT"
        )
    except Exception as e:
        logger.error(f"Error in trading handler: {str(e)}")
        await update.message.reply_text("حدث خطأ في معالجة طلب التداول")
