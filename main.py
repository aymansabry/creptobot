import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from utils.config_loader import ConfigLoader
from utils.logger import logger
from handlers.user_handlers import setup_user_handlers
from handlers.trade_handlers import setup_trade_handlers
from handlers.admin_handlers import setup_admin_handlers
from ai_engine.decision_maker import DecisionMaker
from core.exchange_api import ExchangeAPI
from core.wallet_manager import WalletManager
from core.trade_executor import TradeExecutor
from db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import redis

async def main():
    # تحميل الإعدادات
    config = ConfigLoader()
    
    try:
        # إعداد قاعدة البيانات
        engine = create_async_engine(config.get('database.url'))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        # إعداد Redis
        redis_client = redis.from_url(config.get('redis.url'))
        
        # إعداد واجهات APIs للمنصات
        binance_api = ExchangeAPI(
            api_key=config.get('binance.api_key'),
            api_secret=config.get('binance.api_secret'),
            exchange_name='binance'
        )
        
        kucoin_api = ExchangeAPI(
            api_key=config.get('kucoin.api_key'),
            api_secret=config.get('kucoin.api_secret'),
            exchange_name='kucoin'
        )
        
        # إعداد محرك الذكاء الاصطناعي
        decision_maker = DecisionMaker(exchanges=['binance', 'kucoin'])
        
        # إعداد منفذ الصفقات
        trade_executor = TradeExecutor(binance_api=binance_api, kucoin_api=kucoin_api)
        
        # إعداد تطبيق التليجرام
        application = Application.builder().token(config.get('telegram.bot_token')).build()
        
        # إضافة البيانات المشتركة
        application.bot_data.update({
            'db_session': AsyncSessionLocal,
            'redis_client': redis_client,
            'decision_maker': decision_maker,
            'trade_executor': trade_executor,
            'exchange_api': binance_api,  # نستخدم Binance كافتراضي للسحب والإيداع
            'admin_ids': config.get('telegram.admin_ids'),
            'main_wallet_address': config.get('trading.main_wallet_address'),
            'owner_tron_address': config.get('trading.owner_tron_address')
        })
        
        # إعداد معالجات الأوامر
        setup_user_handlers(application)
        setup_trade_handlers(application)
        setup_admin_handlers(application)
        
        # بدء البوت
        logger.info("Starting the bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # تشغيل البوت حتى يتم إيقافه
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.exception("An error occurred in main:")
    finally:
        if 'application' in locals():
            await application.stop()
            await application.shutdown()
        logger.info("Bot has been stopped")

if __name__ == '__main__':
    asyncio.run(main())
