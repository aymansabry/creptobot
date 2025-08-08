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

async def create_db_tables(application: Application):
    """Create database tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def start_trading_tasks(application: Application):
    """Starts continuous trading loops for users who have it enabled."""
    trade_logic = TradeLogic(application.bot)
    async with async_session() as db_session:
        # Find all users with continuous trading enabled
        result = await db_session.execute(select(Wallet).filter(Wallet.is_continuous_trading == True))
        wallets = result.scalars().all()
        for wallet in wallets:
            # Start a new task for each user
            asyncio.create_task(trade_logic.continuous_trading_loop(wallet.user_id))

def main():
    """Starts the bot."""
    application = Application.builder().token(settings.BOT_TOKEN).pre_init(create_db_tables).post_init(start_trading_tasks).build()
    
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
