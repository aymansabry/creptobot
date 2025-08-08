# project_root/main.py

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from core.config import settings
from handlers import user, admin, common
from ui.buttons import *
from db.database import engine, Base

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_db_tables():
    """Create database tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def main():
    """Starts the bot."""
    application = Application.builder().token(settings.BOT_TOKEN).build()
    
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
    # We create tables before running the bot
    application.run_polling(drop_pending_updates=True,
                            pre_init=create_db_tables)

if __name__ == '__main__':
    main()
