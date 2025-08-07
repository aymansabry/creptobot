import asyncio
import logging
from telegram.ext import Application
from utils.config_loader import ConfigLoader
from handlers.user_handlers import setup_user_handlers
from handlers.trade_handlers import setup_trade_handlers
from handlers.admin_handlers import setup_admin_handlers
from ai_engine.decision_maker import DecisionMaker
from core.exchange_api import ExchangeAPI
from core.trade_executor import TradeExecutor
from db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import redis

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    application = None
    try:
        # تحميل الإعدادات
        config = ConfigLoader()

        # إعداد قاعدة البيانات
        db_url = config.get('database.url')
        if not db_url:
            raise ValueError("❌ لم يتم العثور على رابط قاعدة البيانات في الإعدادات.")
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True
        )

        # إنشاء الجداول
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # جلسة قاعدة البيانات
        AsyncSessionLocal = sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

        # Redis
        redis_url = config.get('redis.url')
        redis_client = redis.from_url(redis_url)

        # إعداد واجهة Binance
        binance_api = ExchangeAPI(
            api_key=config.get('binance.api_key'),
            api_secret=config.get('binance.api_secret'),
            exchange_name='binance'
        )

        # محرك القرارات
        decision_maker = DecisionMaker(exchanges=['binance'])

        # منفذ التداول
        trade_executor = TradeExecutor(binance_api=binance_api)

        # بوت تليجرام
        bot_token = config.get('telegram.bot_token')
        if not bot_token:
            raise ValueError("❌ لم يتم العثور على توكن بوت التليجرام.")
        application = Application.builder() \
            .token(bot_token) \
            .concurrent_updates(True) \
            .build()

        # مشاركة البيانات
        application.bot_data.update({
            'db_session': AsyncSessionLocal,
            'redis_client': redis_client,
            'decision_maker': decision_maker,
            'trade_executor': trade_executor,
            'admin_ids': config.get('telegram.admin_ids'),
            'main_wallet_address': config.get('trading.main_wallet_address')
        })

        # تسجيل المعالجات
        setup_user_handlers(application)
        setup_trade_handlers(application)
        setup_admin_handlers(application)

        # بدء التشغيل
        logger.info("🚀 Starting the bot...")
        await application.initialize()
        await application.bot.delete_webhook()
        await application.start()
        await application.updater.start_polling()

        # البقاء في التشغيل
        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.exception("❌ Fatal error in main:")
    finally:
        if application:
            try:
                await application.stop()
                await application.shutdown()
            except RuntimeError as e:
                logger.warning(f"⚠️ Shutdown issue: {e}")
        logger.info("✅ Bot has been stopped.")

if __name__ == '__main__':
    asyncio.run(main())