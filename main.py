import asyncio
import logging
from telegram.ext import ApplicationBuilder
from core.config import load_config
from db.database import init_db
from core.ai import DecisionMaker
from core.trading import TradeExecutor
from handlers.admin_handlers import setup_admin_handlers
from handlers.user_handlers import setup_user_handlers
from handlers.trade_handlers import setup_trade_handlers
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def main():
    try:
        config = load_config()

        # إعداد قاعدة البيانات
        db_url = config.get("database.url")
        if not db_url:
            raise ValueError("❌ لم يتم العثور على إعداد الاتصال بقاعدة البيانات.")
        engine = create_async_engine(db_url, echo=False)
        db_session = async_sessionmaker(engine, expire_on_commit=False)
        await init_db(engine)

        # إعداد بوت تيليجرام
        token = config.get("telegram.token")
        if not token:
            raise ValueError("❌ لم يتم العثور على توكن البوت.")
        application = ApplicationBuilder().token(token).build()

        # إعداد الذكاء الاصطناعي والتنفيذ
        binance_api_key = config.get("binance.api_key")
        binance_api_secret = config.get("binance.api_secret")
        main_wallet = config.get("trading.main_wallet_address")

        decision_maker = DecisionMaker(api_key=binance_api_key, api_secret=binance_api_secret)
        trade_executor = TradeExecutor(api_key=binance_api_key, api_secret=binance_api_secret, main_wallet=main_wallet)

        # إعداد بيانات مشتركة
        application.bot_data["decision_maker"] = decision_maker
        application.bot_data["trade_executor"] = trade_executor
        application.bot_data["db_session"] = db_session
        application.bot_data["admin_ids"] = config.get("admin.ids", [])

        # إعداد المعالجات
        setup_user_handlers(application)
        setup_trade_handlers(application)
        setup_admin_handlers(application)

        logger.info("🤖 البوت بدأ بنجاح.")
        await application.run_polling()

    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())