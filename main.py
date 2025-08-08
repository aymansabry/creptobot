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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

    trade_logic = TradeLogic(application.bot)
    async with async_session() as db_session:
        result = await db_session.execute(select(Wallet).filter(Wallet.is_continuous_trading == True))
        wallets = result.scalars().all()
        for wallet in wallets:
            asyncio.create_task(trade_logic.continuous_trading_loop(wallet.user_id))
    logger.info("Continuous trading tasks started for all active users.")

def main():
    """Starts the bot."""
    application = Application.builder().token(settings.BOT_TOKEN).post_init(init_and_start_tasks).build()
    
    # --- Register Handlers ---
    # Common handlers
    application.add_handler(CommandHandler("start", common.start))
    application.add_handler(MessageHandler(filters.Regex(BACK_TO_MAIN), common.start))
    
    # User handlers
    application.add_handler(MessageHandler(filters.Regex(START_TRADING), user.handle_start_trading))
    application.add_handler(MessageHandler(filters.Regex(TRIAL_TRADE), user.handle_trial_trade))
    application.add_handler(MessageHandler(filters.Regex(REAL_TRADE), user.handle_real_trade))
    application.add_handler(MessageHandler(filters.Regex(AUTO_TRADE), user.handle_auto_trade))
    application.add_handler(MessageHandler(filters.Regex(MANUAL_TRADE), user.handle_manual_trade))
    application.add_handler(MessageHandler(filters.Regex(VIEW_BALANCE), user.handle_view_balance))
    application.add_handler(MessageHandler(filters.Regex(DEPOSIT_WITHDRAW), user.handle_deposit_withdraw))
    
    # Handlers for deposit/withdraw requests via text messages
    application.add_handler(MessageHandler(filters.Regex(r"^إيداع\s+\d+(\.\d+)?$"), user.handle_deposit_request))
    application.add_handler(MessageHandler(filters.Regex("تم الإيداع"), user.handle_deposit_confirmation))
    application.add_handler(MessageHandler(filters.Regex(r"^سحب\s+\d+(\.\d+)?$"), user.handle_withdraw_request))
    
    # Admin handlers
    application.add_handler(CommandHandler("admin", admin.handle_admin_panel))
    application.add_handler(MessageHandler(filters.Regex(VIEW_USERS), admin.handle_view_users))
    application.add_handler(MessageHandler(filters.Regex(SWITCH_TO_USER), admin.handle_switch_to_user))
    application.add_handler(MessageHandler(filters.Regex(SETTINGS), admin.handle_settings))
    
    # Run the bot
    logger.info("Bot started successfully.")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
