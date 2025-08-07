import logging
from datetime import datetime
import sys

def setup_logging():
    """تهيئة نظام التسجيل الموحد"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# إنشاء جميع اللوغرات المطلوبة
exchange_logger = logging.getLogger('exchange')
trade_logger = logging.getLogger('trade')
wallet_logger = logging.getLogger('wallet')
performance_logger = logging.getLogger('performance')

# إعداد معالجات لكل لوغر
def configure_logger(logger, level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

# تطبيق الإعدادات على جميع اللوغرات
configure_logger(exchange_logger)
configure_logger(trade_logger)
configure_logger(wallet_logger)
configure_logger(performance_logger)

# دالة مساعدة لتسجيل الأخطاء
def log_error(error_msg, logger_name='trade', exc_info=None):
    logger = {
        'trade': trade_logger,
        'wallet': wallet_logger,
        'exchange': exchange_logger,
        'performance': performance_logger
    }.get(logger_name, trade_logger)
    
    logger.error(error_msg, exc_info=exc_info)
