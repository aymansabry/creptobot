# app/services/investment.py
from app.database.models import Investment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

class InvestmentService:

    @staticmethod
    async def create_investment(session: AsyncSession, user_id: int, amount: float, profit_rate: float):
        investment = Investment(
            user_id=user_id,
            amount=amount,
            profit_rate=profit_rate,
            start_time=datetime.utcnow(),
            status="active"
        )
        session.add(investment)
        await session.commit()
        return investment

    @staticmethod
    async def get_user_investments(session: AsyncSession, user_id: int):
        result = await session.execute(select(Investment).where(Investment.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def get_active_investments(session: AsyncSession):
        result = await session.execute(select(Investment).where(Investment.status == "active"))
        return result.scalars().all()
