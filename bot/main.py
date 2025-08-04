import logging
from telegram.ext import Application
from handlers import setup_handlers  # Direct import
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    try:
        app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        setup_handlers(app)
        logging.info("Starting bot in polling mode...")
        app.run_polling()
    except Exception as e:
        logging.error(f"Bot failed: {e}")

if __name__ == '__main__':
    main()
