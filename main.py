import asyncio
import logging
from telegram.ext import ApplicationBuilder
from utils.config_loader import ConfigLoader
from db.database import init_db
from core.ai import DecisionMaker
from core.trading import TradeExecutor
from handlers.admin_handlers import setup_admin_handlers
from handlers.user_handlers import setup_user_handlers
from handlers.trade_handlers import setup_trade_handlers
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def main():
    try:
        config = ConfigLoader()

        # إعداد قاعدة البيانات
        db_url = config.get("DATABASE_URL")
        if not db_url:
            raise ValueError("❌ DATABASE_URL is missing in environment variables.")
        engine = create_async_engine(db_url, echo=False)
        db_session = async_sessionmaker(engine, expire_on_commit=False)
        await init_db(engine)

        # إعداد بوت تيليجرام
        token = config.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN is missing in environment variables.")
        application = ApplicationBuilder().token(token).build()

        # إعداد الذكاء الاصطناعي والتنفيذ
        binance_api_key = config.get("BINANCE_API_KEY")
        binance_api_secret = config.get("BINANCE_API_SECRET")
        main_wallet = config.get("TRADING_MAIN_WALLET_ADDRESS")

        decision_maker = DecisionMaker(api_key=binance_api_key, api_secret=binance_api_secret)
        trade_executor = TradeExecutor(api_key=binance_api_key, api_secret=binance_api_secret, main_wallet=main_wallet)

        # تحميل معرفات الإدمن كقائمة
        admin_ids_raw = config.get("TELEGRAM_ADMIN_IDS", "")
        admin_ids = [int(uid.strip()) for uid in admin_ids_raw.split(",") if uid.strip().isdigit()]

        # تمرير البيانات للمعالجات
        application.bot_data["decision_maker"] = decision_maker
        application.bot_data["trade_executor"] = trade_executor
        application.bot_data["db_session"] = db_session
        application.bot_data["admin_ids"] = admin_ids

        # إعداد المعالجات
        setup_user_handlers(application)
        setup_trade_handlers(application)
        setup_admin_handlers(application)

        logger.info("✅ Bot started successfully.")
        await application.run_polling()

    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())