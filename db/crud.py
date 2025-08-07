from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Optional, List, Any
import uuid
from .models import User, Wallet, Trade, ContinuousInvestment, SystemSettings

async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalars().first()

async def create_user(session: AsyncSession, user_data: Dict[str, Any]) -> User:
    user = User(**user_data)
    session.add(user)
    await session.commit()
    return user

async def get_user_wallet(session: AsyncSession, user_id: int) -> Optional[Wallet]:
    result = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalars().first()

async def create_wallet(session: AsyncSession, wallet_data: Dict[str, Any]) -> Wallet:
    wallet = Wallet(**wallet_data)
    session.add(wallet)
    await session.commit()
    return wallet

async def update_wallet_balance(session: AsyncSession, user_id: int, balances: Dict[str, float]) -> Wallet:
    wallet = await get_user_wallet(session, user_id)
    if wallet:
        wallet.balances = balances
        await session.commit()
    return wallet

async def create_trade_record(session: AsyncSession, trade_data: Dict[str, Any]) -> Trade:
    trade_data['trade_uuid'] = str(uuid.uuid4())
    trade = Trade(**trade_data)
    session.add(trade)
    await session.commit()
    return trade

async def get_user_trades(session: AsyncSession, user_id: int, limit: int = 10) -> List[Trade]:
    result = await session.execute(
        select(Trade)
        .where(Trade.user_id == user_id)
        .order_by(Trade.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def create_continuous_investment(session: AsyncSession, investment_data: Dict[str, Any]) -> ContinuousInvestment:
    investment = ContinuousInvestment(**investment_data)
    session.add(investment)
    await session.commit()
    return investment

async def get_continuous_investment(session: AsyncSession, user_id: int) -> Optional[ContinuousInvestment]:
    result = await session.execute(
        select(ContinuousInvestment)
        .where(ContinuousInvestment.user_id == user_id)
    )
    return result.scalars().first()

async def update_continuous_investment(session: AsyncSession, user_id: int, updates: Dict[str, Any]) -> ContinuousInvestment:
    investment = await get_continuous_investment(session, user_id)
    if investment:
        for key, value in updates.items():
            setattr(investment, key, value)
        await session.commit()
    return investment

async def get_system_settings(session: AsyncSession) -> SystemSettings:
    result = await session.execute(select(SystemSettings).limit(1))
    settings = result.scalars().first()
    if not settings:
        settings = SystemSettings()
        session.add(settings)
        await session.commit()
    return settings

async def update_system_settings(session: AsyncSession, updates: Dict[str, Any], updated_by: int = None) -> SystemSettings:
    settings = await get_system_settings(session)
    
    for key, value in updates.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    if updated_by:
        settings.updated_by = updated_by
    
    await session.commit()
    return settings
