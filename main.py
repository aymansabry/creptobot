import asyncio
import logging
from telegram.ext import Application
from utils.config_loader import ConfigLoader
from utils.logger import logger
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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Load configuration
        config = ConfigLoader()
        
        # Database setup
        engine = create_async_engine(
            config.get('database.url'),
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Session factory
        AsyncSessionLocal = sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        # Redis setup
        redis_client = redis.from_url(config.get('redis.url'))
        
        # Exchange APIs setup
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
        
        # AI Engine setup
        decision_maker = DecisionMaker(exchanges=['binance', 'kucoin'])
        
        # Trade executor setup
        trade_executor = TradeExecutor(binance_api=binance_api, kucoin_api=kucoin_api)
        
        # Telegram application setup
        application = Application.builder() \
            .token(config.get('telegram.bot_token')) \
            .build()
        
        # Share data between handlers
        application.bot_data.update({
            'db_session': AsyncSessionLocal,
            'redis_client': redis_client,
            'decision_maker': decision_maker,
            'trade_executor': trade_executor,
            'exchange_api': binance_api,
            'admin_ids': config.get('telegram.admin_ids'),
            'main_wallet_address': config.get('trading.main_wallet_address'),
            'owner_tron_address': config.get('trading.owner_tron_address')
        })
        
        # Setup handlers
        setup_user_handlers(application)
        setup_trade_handlers(application)
        setup_admin_handlers(application)
        
        # Start the bot
        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.exception("Fatal error in main:")
    finally:
        if 'application' in locals():
            await application.stop()
            await application.shutdown()
        logger.info("Bot stopped")

if __name__ == '__main__':
    asyncio.run(main())
