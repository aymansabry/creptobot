from app.utils.binance_utils import verify_transaction
from app.database.models import Transaction, User
from app.database.db import get_session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def log_transaction(user_id: int, amount: float, tx_hash: str, session: AsyncSession):
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        tx_hash=tx_hash,
        confirmed=False,
        timestamp=datetime.utcnow()
    )
    session.add(transaction)
    await session.commit()
    return transaction

async def confirm_transaction(tx_hash: str, session: AsyncSession):
    result = await verify_transaction(tx_hash)
    if not result:
        return False

    q = await session.execute(select(Transaction).where(Transaction.tx_hash == tx_hash))
    transaction = q.scalar_one_or_none()
    if transaction:
        transaction.confirmed = True
        await session.commit()
        return True
    return False
