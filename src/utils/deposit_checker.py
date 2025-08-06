from decimal import Decimal
from src.database.models_helpers import update_user_wallet_balance
from src.utils.wallet_tools import generate_mock_wallet_address

# مبدئيًا يتم التحقق الوهمي فقط
MOCK_NETWORK_BALANCES = {}

async def simulate_deposit(telegram_id: int, amount: Decimal):
    MOCK_NETWORK_BALANCES[telegram_id] = amount
    await update_user_wallet_balance(telegram_id, amount)

async def get_wallet_balance(telegram_id: int) -> Decimal:
    return MOCK_NETWORK_BALANCES.get(telegram_id, Decimal("0.0"))
