from src.database.models import async_session, User, Wallet, Investment, Settings
from sqlalchemy.future import select
from decimal import Decimal

async def get_user_wallet(telegram_id: int):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None
        return user.wallet

async def update_user_wallet_balance(telegram_id: int, new_balance: Decimal):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.wallet.balance = new_balance
            await session.commit()

async def save_investment_transaction(telegram_id: int, amount: Decimal, net_profit: Decimal, bot_fee: Decimal):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return

        tx = Investment(user_id=user.id, amount=amount, net_profit=net_profit, bot_fee=bot_fee)
        session.add(tx)
        await session.commit()

async def get_total_investment_stats():
    async with async_session() as session:
        total_users = await session.execute(select(User))
        total_profits = await session.execute(select(Investment.net_profit))
        investors = await session.execute(select(Investment.user_id).distinct())

        total_users_count = len(total_users.scalars().all())
        total_profits_sum = sum(total_profits.scalars().all() or [0])
        investor_count = len(investors.scalars().all())

        return {
            "total_users": total_users_count,
            "total_profits": total_profits_sum,
            "investors": investor_count
        }

async def set_profit_percentage(p: float):
    async with async_session() as session:
        stmt = select(Settings).where(Settings.key == "profit_percentage")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if not setting:
            setting = Settings(key="profit_percentage", value=str(p))
            session.add(setting)
        else:
            setting.value = str(p)
        await session.commit()

async def get_profit_percentage() -> float:
    async with async_session() as session:
        stmt = select(Settings).where(Settings.key == "profit_percentage")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        return float(setting.value) if setting else 10.0
