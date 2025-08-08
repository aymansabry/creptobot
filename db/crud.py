# project_root/db/crud.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import User, Wallet, Trade
from typing import Optional
from datetime import datetime

async def create_user(db_session: AsyncSession, telegram_id: int, username: str, is_admin: bool = False) -> User:
    """Creates a new user and their wallet."""
    user = User(telegram_id=telegram_id, username=username, is_admin=is_admin)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    wallet = Wallet(user_id=user.id)
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)
    
    return user

async def get_user_by_telegram_id(db_session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Retrieves a user by their Telegram ID."""
    result = await db_session.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def get_wallet_by_user_id(db_session: AsyncSession, user_id: int) -> Optional[Wallet]:
    """Retrieves a wallet by its user ID."""
    result = await db_session.execute(select(Wallet).filter(Wallet.user_id == user_id))
    return result.scalar_one_or_none()

async def update_wallet_balance(db_session: AsyncSession, wallet_id: int, amount: float):
    """Updates a wallet's balance by adding/subtracting an amount."""
    wallet = await db_session.get(Wallet, wallet_id)
    if wallet:
        wallet.balance_usdt += amount
        await db_session.commit()
        await db_session.refresh(wallet)

async def create_trade(db_session: AsyncSession, trade_data: dict) -> Trade:
    """Creates a new trade record."""
    trade = Trade(**trade_data)
    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(trade)
    return trade

async def get_open_trades(db_session: AsyncSession, wallet_id: int) -> list[Trade]:
    """Retrieves all open trades for a specific wallet."""
    result = await db_session.execute(
        select(Trade).filter(Trade.wallet_id == wallet_id, Trade.status == "open")
    )
    return result.scalars().all()

async def close_trade(db_session: AsyncSession, trade_id: int, exit_price: float, profit: float):
    """Closes an existing trade record and calculates profit."""
    trade = await db_session.get(Trade, trade_id)
    if trade:
        trade.exit_price = exit_price
        trade.profit = profit
        trade.status = "closed"
        trade.closed_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(trade)
