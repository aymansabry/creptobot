from database.investments import mark_investment_completed
from database.users import get_user_wallet, get_owner_wallet
from utils.blockchain import transfer_usdt
from config import settings

async def execute_trade(user_id: int, amount: float, investment_id: int):
    profit_percentage = settings.DEFAULT_PROFIT_PERCENTAGE
    bot_fee_percentage = settings.BOT_FEE_PERCENTAGE

    total_profit = amount * (profit_percentage / 100)
    bot_fee = total_profit * (bot_fee_percentage / 100)
    user_profit = total_profit - bot_fee

    user_wallet = await get_user_wallet(user_id)
    owner_wallet = await get_owner_wallet()

    await transfer_usdt(user_wallet, amount + user_profit)
    await transfer_usdt(owner_wallet, bot_fee)

    await mark_investment_completed(investment_id)
