# app/services/admin.py
from app.database.models import AdminConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class AdminService:

    @staticmethod
    async def get_profit_percentage(session: AsyncSession):
        result = await session.execute(select(AdminConfig))
        config = result.scalar_one_or_none()
        return config.profit_percentage if config else 0.05

    @staticmethod
    async def update_profit_percentage(session: AsyncSession, new_percentage: float):
        result = await session.execute(select(AdminConfig))
        config = result.scalar_one_or_none()
        if config:
            config.profit_percentage = new_percentage
        else:
            config = AdminConfig(profit_percentage=new_percentage)
            session.add(config)
        await session.commit()
        return True
