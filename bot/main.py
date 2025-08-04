from handlers import setup_handlers
from config import Config
from telegram.ext import Application
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    setup_handlers(application)
    application.run_polling()

if __name__ == '__main__':
    main()
