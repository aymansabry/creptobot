from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from handlers import start, button_handler
from db import init_db
import os
from dotenv import load_dotenv

load_dotenv()
init_db()

def main():
    updater = Updater(os.getenv("BOT_TOKEN"), use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()