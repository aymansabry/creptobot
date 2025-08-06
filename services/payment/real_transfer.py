from apis.tron import TronNetwork
from core.security import SecureVault

class PaymentGateway:
    def __init__(self, config):
        vault = SecureVault(config.ENCRYPTION_KEY)
        self.tron = TronNetwork(
            private_key=vault.decrypt_key(config.TRON_PRIVATE_KEY)
        )
    
    async def distribute_profits(self, user_wallet: str, amount: float):
        """توزيع الأرباح مع خصم عمولة البوت"""
        bot_share = amount * 0.015  # 1.5% عمولة
        user_share = amount - bot_share
        
        # تحويل عمولة البوت
        await self.tron.send_usdt(config.ADMIN_WALLET, bot_share)
        
        # تحويل ربح المستخدم
        receipt = await self.tron.send_usdt(user_wallet, user_share)
        return receipt
