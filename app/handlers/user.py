from aiogram import Router, types, F
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.wallet import generate_virtual_wallet
from app.database.models import User

user_router = Router()

@user_router.message(CommandStart())
async def start(message: types.Message, session: AsyncSession):
    user = await session.scalar(
        session.execute(User.__table__.select().where(User.telegram_id == message.from_user.id))
    )
    if not user:
        new_user = User(telegram_id=message.from_user.id, wallet_address=generate_virtual_wallet())
        session.add(new_user)
        await session.commit()
        await message.answer("تم تسجيلك بنجاح وإنشاء محفظتك الوهمية.")
    else:
        await message.answer(f"مرحباً بعودتك! محفظتك: {user.wallet_address}")
