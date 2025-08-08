# project_root/main.py

import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from core.config import settings
from handlers import user, admin, common
from ui.buttons import *
from db.database import engine, async_session
from db.models import Base, Wallet
from sqlalchemy.future import select
from services.trade_logic import TradeLogic

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def init_and_start_tasks(application: Application):
    """Initializes the database tables and starts continuous trading loops."""
    # 1. Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

    # 2. Start continuous trading tasks
    trade_logic = TradeLogic(application.bot)
    async with async_session() as db_session:
        result = await db_session.execute(select(Wallet).filter(Wallet.is_continuous_trading == True))
        wallets = result.scalars().all()
        for wallet in wallets:
            asyncio.create_task(trade_logic.continuous_trading_loop(wallet.user_id))
    logger.info("Continuous trading tasks started for all active users.")

def main():
    """Starts the bot."""
    # Build the application with a single post_init function
    application = Application.builder().token(settings.BOT_TOKEN).post_init(init_and_start_tasks).build()

    # --- Register Handlers ---
    # Common handlers
    application.add_handler(CommandHandler("start", common.start))

    # User handlers
    application.add_handler(MessageHandler(filters.Regex(START_TRADING), user.handle_start_trading))
    application.add_handler(MessageHandler(filters.Regex(AUTO_TRADE), user.handle_auto_trade))
    application.add_handler(MessageHandler(filters.Regex(MANUAL_TRADE), user.handle_manual_trade))
    application.add_handler(MessageHandler(filters.Regex(VIEW_BALANCE), user.handle_view_balance))
    application.add_handler(MessageHandler(filters.Regex(BACK_TO_MAIN), common.start))

    # Admin handlers
    application.add_handler(CommandHandler("admin", admin.handle_admin_panel))
    application.add_handler(MessageHandler(filters.Regex(VIEW_USERS), admin.handle_view_users))

    # Run the bot
    logger.info("Bot started successfully.")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
