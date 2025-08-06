import telegram
from core.config import Config

bot = telegram.Bot(token=Config.TELEGRAM_TOKEN)

def send_notification(user_id: str, message: str):
    try:
        bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Failed to send notification: {str(e)}")
