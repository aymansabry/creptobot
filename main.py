from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from menus.user.main_menu import show_main_menu
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def start(update, context):
    show_main_menu(update)

def main():
    updater = Updater(token=os.getenv('TELEGRAM_TOKEN'), use_context=True)
    dp = updater.dispatcher
    
    # Handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, start))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
