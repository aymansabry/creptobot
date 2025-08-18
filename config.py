import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # إعدادات أساسية
    BOT_TOKEN = os.environ['BOT_TOKEN']  # مطلوب
    
    # إعدادات التداول (قيم افتراضية آمنة)
    TRADE_PERCENT = float(os.getenv('BOT_PERCENT', '1.0'))
    MIN_INVEST = float(os.getenv('MIN_INVEST_AMOUNT', '10.0'))
    MAX_INVEST = float(os.getenv('MAX_INVEST_AMOUNT', '1000.0'))
    
    @staticmethod
    def show_settings():
        return (
            f"✅ البوت يعمل بنجاح\n"
            f"نسبة التداول: {Config.TRADE_PERCENT}%\n"
            f"حدود الاستثمار: {Config.MIN_INVEST}-{Config.MAX_INVEST} USDT"
        )

# تحقق من وجود التوكن الأساسي
if not Config.BOT_TOKEN:
    logger.error("يجب تعيين متغير البيئة BOT_TOKEN")
    exit(1)