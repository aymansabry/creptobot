# main.py

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
        # تحميل الإعدادات من متغيرات البيئة مباشرة
        config = ConfigLoader()

        # إعداد قاعدة البيانات
        engine = create_async_engine(
            config.get("database.url"),
            echo=False,
            pool_pre_ping=True
        )

        # إنشاء الجداول في حال لم تكن موجودة
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # جلسة قاعدة البيانات
        AsyncSessionLocal = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Redis
        redis_client = redis.from_url(config.get("redis.url"))

        # Binance API
        binance_api = ExchangeAPI(
            api_key=config.get("binance.api_key"),
            api_secret=config.get("binance.api_secret"),
            exchange_name="binance"
        )

        # AI Decision Engine
        decision_maker = DecisionMaker(exchanges=["binance"])

        # منفذ الصفقات
        trade_executor = TradeExecutor(binance_api=binance_api)

        # بوت تيليجرام
        application = Application.builder() \
            .token(config.get("telegram.bot_token")) \
            .concurrent_updates(True) \
            .build()

        # مشاركة البيانات بين المعالجات
        application.bot_data.update({
            "db_session": AsyncSessionLocal,
            "redis_client": redis_client,
            "decision_maker": decision_maker,
            "trade_executor": trade_executor,
            "admin_ids": config.get("telegram.admin_ids"),
            "main_wallet_address": config.get("trading.main_wallet_address"),
        })

        # تسجيل المعالجات
        setup_user_handlers(application)
        setup_trade_handlers(application)
        setup_admin_handlers(application)

        logger.info("Starting the bot...")
        await application.initialize()
        await application.bot.delete_webhook()
        await application.start()
        await application.updater.start_polling()

        # حلقة تشغيل دائمة
        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.exception("Fatal error in main:")
    finally:
        if 'application' in locals():
            try:
                await application.stop()
                await application.shutdown()
            except RuntimeError as e:
                logger.warning(f"Shutdown warning: {e}")
        logger.info("Bot has been stopped")

if __name__ == "__main__":
    asyncio.run(main())