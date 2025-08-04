import logging
from telegram.ext import Application
from handlers import setup_handlers  # Now using direct import
from config import Config

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    try:
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        setup_handlers(application)
        application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()
