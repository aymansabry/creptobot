from tronpy import Tron
from config import config

class PaymentGateway:
    def __init__(self, config):
        self.client = Tron(network='mainnet')
        self.private_key = config.TRON_PRIVATE_KEY
    
    async def distribute_profits(self, user_id: int, amount: float):
        bot_share = amount * config.BOT_COMMISSION
        user_share = amount - bot_share
        
        # تحويل عمولة البوت
        await self._send_usdt(config.ADMIN_WALLET, bot_share)
        
        # تحويل ربح المستخدم (يجب استبدال بمحفظة المستخدم الفعلية)
        await self._send_usdt("USER_TRON_WALLET", user_share)
    
    async def _send_usdt(self, to_address: str, amount: float):
        contract = self.client.get_contract(config.TRON_USDT_CONTRACT)
        txn = (
            contract.functions.transfer(to_address, int(amount * 1_000_000))
            .with_owner(config.ADMIN_WALLET)
            .build()
            .sign(self.private_key)
        )
        return txn.broadcast()
