from aiogram import types
from database.models import User
from database import get_db

async def create_wallet(message: types.Message):
    async with get_db() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(id=message.from_user.id, wallet="TXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            session.add(user)
            await session.commit()
            await message.answer("🎉 تم إنشاء محفظتك!")
        else:
            await message.answer("⚠️ لديك محفظة بالفعل!")
