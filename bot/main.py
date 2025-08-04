from telegram.ext import Application
from handlers import setup_handlers
from config import Config
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    setup_handlers(app)
    app.run_polling()

if __name__ == '__main__':
    main()
