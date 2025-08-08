# project_root/db/crud.py

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import models

async def get_user(db_session: AsyncSession, user_id: int):
    """Fetches a user from the database by user_id."""
    result = await db_session.execute(
        select(models.User).filter(models.User.user_id == user_id)
    )
    return result.scalars().first()

async def create_user(db_session: AsyncSession, user_id: int, username: str):
    """Creates a new user in the database."""
    user = models.User(user_id=user_id, username=username)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

async def get_wallet_by_user_id(db_session: AsyncSession, user_id: int):
    """Fetches a user's wallet from the database."""
    result = await db_session.execute(
        select(models.Wallet).filter(models.Wallet.user_id == user_id)
    )
    return result.scalars().first()
    
async def create_wallet(db_session: AsyncSession, user_id: int):
    """Creates a new wallet for a user."""
    wallet = models.Wallet(user_id=user_id)
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)
    return wallet

# Placeholder for other functions
async def create_trade(db_session: AsyncSession, trade_data: dict):
    pass
    
async def get_open_trades(db_session: AsyncSession, wallet_id: int):
    pass
    
async def close_trade(db_session: AsyncSession, trade_id: int, exit_price: float, profit: float):
    pass
