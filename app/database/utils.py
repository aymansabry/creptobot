# app/database/utils.py
from app.database.session import SessionLocal
from app.database.models import User
from sqlalchemy.future import select


async def get_or_create_user(telegram_id: int, username: str = None):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user
