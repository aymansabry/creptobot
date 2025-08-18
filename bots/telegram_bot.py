from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from core.exchanges import BinanceExchange
from db import crud, database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text('مرحباً بكم في بوت المراجحة الآلي')

def handle_api_keys(update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    
    try:
        exchange, api_key, api_secret = text.split()
        with database.SessionLocal() as db:
            crud.update_exchange_api(db, user_id, exchange, {
                'api_key': api_key,
                'api_secret': api_secret,
                'is_valid': True
            })
        update.message.reply_text(f'تم تحديث مفاتيح {exchange} بنجاح')
    except Exception as e:
        logger.error(f"API key update error: {e}")
        update.message.reply_text('خطأ في إدخال المفاتيح')

def main():
    updater = Updater(Config.BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_api_keys))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()