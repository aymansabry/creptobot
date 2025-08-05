# app/services/wallet.py
from app.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class WalletService:

    @staticmethod
    async def get_user_wallet(session: AsyncSession, user_id: int):
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user.wallet_balance
        return 0.0

    @staticmethod
    async def update_user_wallet(session: AsyncSession, user_id: int, amount: float):
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.wallet_balance += amount
            await session.commit()
            return True
        return False
