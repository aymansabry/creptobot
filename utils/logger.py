import logging
from datetime import datetime
import sys

class Logger:
    def __init__(self):
        self.setup_logging()
        
        # إنشاء جميع اللوغرات المطلوبة
        self.exchange = logging.getLogger('exchange')
        self.trade = logging.getLogger('trade')
        self.wallet = logging.getLogger('wallet')
        self.user = logging.getLogger('user')
        self.performance = logging.getLogger('performance')

        # تهيئة جميع اللوغرات
        self._configure_all_loggers()

    def setup_logging(self):
        """تهيئة الإعدادات الأساسية للتسجيل"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _configure_logger(self, logger, level=logging.INFO):
        """تهيئة لوغر فردي"""
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False

    def _configure_all_loggers(self):
        """تهيئة جميع اللوغرات"""
        self._configure_logger(self.exchange)
        self._configure_logger(self.trade)
        self._configure_logger(self.wallet)
        self._configure_logger(self.user)
        self._configure_logger(self.performance)

# تهيئة النظام الأساسي
logger = Logger()

# إختصارات للوغرات
exchange_logger = logger.exchange
trade_logger = logger.trade
wallet_logger = logger.wallet
user_logger = logger.user
performance_logger = logger.performance

def log_error(error_msg, logger_name='system', exc_info=None):
    """دالة مركزية لتسجيل الأخطاء"""
    logger_mapping = {
        'exchange': exchange_logger,
        'trade': trade_logger,
        'wallet': wallet_logger,
        'user': user_logger,
        'performance': performance_logger,
        'system': logging.getLogger('system')
    }
    
    selected_logger = logger_mapping.get(logger_name, logging.getLogger('system'))
    selected_logger.error(error_msg, exc_info=exc_info)
