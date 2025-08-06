from aiogram import types
from database.operations import create_user
from database.models import User

async def create_wallet(message: types.Message):
    # إنشاء محفظة حقيقية هنا (يجب استبدالها بوظيفة TRON الفعلية)
    dummy_wallet = "T" + "X"*33  # مثال لعنوان محفظة
    await create_user(message.from_user.id, dummy_wallet)
    await message.answer(f"🎉 تم إنشاء محفظتك:\n{dummy_wallet}")
