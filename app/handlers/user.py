# app/handlers/user.py
from aiogram import Router, F
from aiogram.types import Message
from app.database.utils import get_or_create_user

user_router = Router()


@user_router.message(F.text)
async def handle_user_message(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(f"أهلًا {message.from_user.first_name}!\nرصيدك الحالي: {user.balance} USDT.")
