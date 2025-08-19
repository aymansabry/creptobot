from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from bot.handlers import main_menu
from bot.arbitrage_callback import handle_run_arbitrage

def start(update, context):
    update.message.reply_text("👋 مرحبًا بك! اختر من القائمة:", reply_markup=main_menu())

def main():
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_run_arbitrage, pattern='^run_arbitrage$'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
