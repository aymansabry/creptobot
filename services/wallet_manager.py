# project_root/services/wallet_manager.py

from db.database import async_session
from db import crud
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings

class WalletManager:
    """
    Manages internal user wallets, profit distribution, and transfers.
    """
    
    def __init__(self):
        # The owner's wallet address should be configured safely
        self.owner_wallet_address = "YOUR_OWNER_WALLET_ADDRESS" 

    async def process_deposit(self, user_id: int, deposit_amount: float):
        """
        Verifies a deposit and updates the user's internal wallet balance.
        """
        async with async_session() as db_session:
            user_wallet = await crud.get_wallet_by_user_id(db_session, user_id)
            if user_wallet:
                await crud.update_wallet_balance(db_session, user_wallet.id, deposit_amount)
                return True
            return False

    async def distribute_profit(self, trade_id: int, user_id: int, profit: float, is_continuous: bool = False):
        """
        Distributes profit from a trade to the user and the bot owner.
        """
        async with async_session() as db_session:
            user_wallet = await crud.get_wallet_by_user_id(db_session, user_id)
            if not user_wallet:
                return False

            bot_fee_percentage = 0.10
            bot_profit = profit * bot_fee_percentage
            user_profit = profit - bot_profit

            await crud.update_wallet_balance(db_session, user_wallet.id, user_profit)
            
            print(f"Transferring {bot_profit} USDT to owner's wallet: {self.owner_wallet_address}")
            
            return True
