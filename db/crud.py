from sqlalchemy.future import select
from db.models import User
from db.database import AsyncSessionLocal

async def get_user_by_telegram_id(telegram_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()
