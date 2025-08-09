from telegram import Bot
from core.config import BOT_TOKEN

class NotificationService:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)

    async def send_notification(self, chat_id: int, message: str):
        await self.bot.send_message(chat_id=chat_id, text=message)
