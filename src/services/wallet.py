from src.database.models import get_user_wallet
from decimal import Decimal

async def get_client_wallet_balance(user_id: int) -> Decimal:
    wallet = await get_user_wallet(user_id)
    return wallet.balance if wallet else Decimal("0.0")
