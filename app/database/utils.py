from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models import User, Wallet
from app.database.session import SessionLocal


async def get_or_create_user(user_id: int, username: str, full_name: str) -> User:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalars().first()
        if not user:
            user = User(telegram_id=user_id, username=username, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_total_users() -> int:
    async with SessionLocal() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()


async def get_total_balance() -> float:
    async with SessionLocal() as session:
        result = await session.execute(select(func.sum(Wallet.balance)))
        total = result.scalar()
        return float(total) if total else 0.0
