import logging
from telegram.ext import Application
from bot.handlers import setup_handlers
from bot.config import Config
from bot.database import init_db

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(app):
    """Initialize application components"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Application startup complete")

def main():
    """Run the bot"""
    try:
        # Create Application
        application = Application.builder() \
            .token(Config.TELEGRAM_TOKEN) \
            .post_init(post_init) \
            .build()
        
        # Setup handlers
        setup_handlers(application)
        
        logger.info("Starting bot in polling mode...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
