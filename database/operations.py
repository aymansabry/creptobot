from .models import User
from . import get_db

async def create_user(user_id: int, wallet_address: str):
    async with get_db() as session:
        user = User(id=user_id, wallet=wallet_address)
        session.add(user)
        await session.commit()
