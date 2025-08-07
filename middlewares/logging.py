from aiogram import BaseMiddleware
from aiogram.types import Message
from database.crud import create_log
from logger import logger

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        text = event.text
        logger.info(f"📥 [{user_id}] → {text}")
        await create_log(event=text, user_id=user_id)
        return await handler(event, data)
