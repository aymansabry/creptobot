import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config.settings import settings
from handlers import user_handlers, admin_handlers, trade_handlers
from utils.logger import setup_logger
from services.trade_service import TradeService
from ai.market_analysis import MarketAnalyzer

# إعداد السجل
setup_logger()
logger = logging.getLogger(__name__)

# تهيئة البوت
bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# تسجيل المعالجات
user_handlers.register_handlers(dp)
admin_handlers.register_handlers(dp)
trade_handlers.register_handlers(dp)

# خدمات الخلفية
trade_service = TradeService()
market_analyzer = MarketAnalyzer()

async def on_startup(dp):
    """إجراءات بدء التشغيل"""
    logger.info("بدء تشغيل البوت")
    
    # بدء المهام الدورية
    from utils.scheduler import start_scheduler
    await start_scheduler(dp)

async def on_shutdown(dp):
    """إجراءات إيقاف التشغيل"""
    logger.info("إيقاف البوت")
    await dp.storage.close()
    await dp.storage.wait_closed()
    await bot.close()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
