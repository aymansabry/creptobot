import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    # الإعدادات الأساسية
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # إعدادات المراجحة
    ARB_THRESHOLD = float(os.getenv('ARB_THRESHOLD', '0.5'))  # نسبة المراجحة الدنيا
    SUPPORTED_EXCHANGES = ['binance', 'kucoin']  # المنصات المدعومة
    
    @staticmethod
    def validate():
        if not Config.BOT_TOKEN:
            logger.error("يجب تعيين متغير البيئة BOT_TOKEN")
            raise ValueError("BOT_TOKEN مفقود")

Config.validate()