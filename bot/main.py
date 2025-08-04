from telegram.ext import Application
from core.config import settings
from handlers.user import UserHandler
from handlers.trading import TradingHandler
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def setup_handlers(app):
    user_handler = UserHandler()
    trading_handler = TradingHandler()
    
    app.add_handler(CommandHandler("start", user_handler.start))
    app.add_handler(MessageHandler(filters.TEXT, user_handler.handle_message))

def main():
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    setup_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()
