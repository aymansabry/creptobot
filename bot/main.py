from telegram.ext import Application
from handlers import setup_handlers
from config import Config
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    try:
        app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        setup_handlers(app)
        logging.info("Starting bot with button menu...")
        app.run_polling()
    except Exception as e:
        logging.error(f"Failed to start: {e}")

if __name__ == '__main__':
    main()
