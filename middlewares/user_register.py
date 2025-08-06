from aiogram.types import Message
from aiogram.dispatcher.middlewares import BaseMiddleware
from database.users import get_user_by_telegram_id, add_user

class UserRegisterMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: Message, data: dict):
        tg_id = message.from_user.id
        if not await get_user_by_telegram_id(tg_id):
            await add_user(tg_id=tg_id, username=message.from_user.username)
