from database.investments import get_pending_investments, update_status
from utils.blockchain import check_wallet_received
from services.executor import execute_trade

async def verify_all_transactions():
    investments = await get_pending_investments()
    for inv in investments:
        received = await check_wallet_received(inv.wallet_address, inv.amount)
        if received:
            await execute_trade(user_id=inv.user_id, amount=inv.amount, investment_id=inv.id)
            await update_status(inv.id, "completed")
