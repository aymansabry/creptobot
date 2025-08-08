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
    try:
        # تحميل الإعدادات
        config = ConfigLoader()

        # إعداد قاعدة البيانات
        database_url = config.get('database.url')
        if not database_url:
            raise ValueError("❌ لم يتم العثور على database.url في ملف الإعدادات.")

        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True
        )

        # إنشاء الجداول
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # إعداد جلسة قاعدة البيانات
        AsyncSessionLocal = sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

        # إعداد Redis
        redis_url = config.get('redis.url')
        if not redis_url:
            raise ValueError("❌ لم يتم العثور على redis.url في ملف الإعدادات.")
        redis_client = redis.from_url(redis_url)

        # إعداد API التبادل
        binance_api = ExchangeAPI(
            api_key=config.get('binance.api_key'),
            api_secret=config.get('binance.api_secret'),
            exchange_name='binance'
        )

        # إعداد محرك الذكاء
        decision_maker = DecisionMaker(exchanges=['binance'])

        # إعداد منفذ الصفقات
        trade_executor = TradeExecutor(binance_api=binance_api)

        # إنشاء التطبيق
        application = Application.builder() \
            .token(config.get('telegram.bot_token')) \
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

        # بدء البوت
        logger.info("✅ Bot is starting...")
        await application.initialize()
        await application.bot.delete_webhook()
        await application.start()
        await application.updater.start_polling()

        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.exception("❌ Fatal error in main:")
    finally:
        if 'application' in locals():
            if application.running:
                await application.stop()
                await application.shutdown()
        logger.info("🛑 Bot has been stopped")

if __name__ == '__main__':
    asyncio.run(main())