from aiogram import BaseMiddleware
from aiogram.types import Message
from database.crud import get_or_create_user

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        user = event.from_user
        # تسجيل المستخدم إذا لم يكن مسجلًا
        await get_or_create_user(user)
        return await handler(event, data)
