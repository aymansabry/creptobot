from database import AsyncSessionLocal
from database.models import User
from sqlalchemy import select

async def get_balance(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.balance if user else 0.0