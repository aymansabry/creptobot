from binance.client import Client
from core.config import config
from utils.logger import wallet_logger, log_error
from datetime import datetime
import threading

class VirtualWallet:
    def __init__(self):
        self.client = Client(
            config.BINANCE_API_KEY,
            config.BINANCE_API_SECRET
        )
        self.wallets = {}
        self.lock = threading.Lock()
        wallet_logger.info("Virtual wallet system initialized")
        
    def create_wallet(self, user_id):
        """إنشاء محفظة افتراضية جديدة"""
        with self.lock:
            if user_id not in self.wallets:
                self.wallets[user_id] = {
                    'balance': 0.0,
                    'deposits': [],
                    'created_at': datetime.now().isoformat()
                }
                wallet_logger.info(f"Created new wallet for user {user_id}")
            return self.wallets[user_id]
    
    async def verify_deposit(self, user_id, tx_hash):
        """التحقق من صحة الإيداع على Binance"""
        try:
            deposit = self.client.get_deposit_history(transactionHash=tx_hash)
            if deposit and len(deposit['depositList']) > 0:
                deposit = deposit['depositList'][0]
                if deposit['status'] == 1:  # تم التأكيد
                    amount = float(deposit['amount'])
                    with self.lock:
                        self.wallets[user_id]['balance'] += amount
                        self.wallets[user_id]['deposits'].append({
                            'tx_hash': tx_hash,
                            'amount': amount,
                            'timestamp': datetime.now().isoformat()
                        })
                    wallet_logger.info(f"Deposit confirmed for user {user_id}: {amount} USDT")
                    return True
            wallet_logger.warning(f"Deposit not confirmed for tx_hash: {tx_hash}")
            return False
        except Exception as e:
            log_error(f"Deposit verification failed: {str(e)}", 'wallet')
            return False
    
    def get_balance(self, user_id):
        """الحصول على رصيد المحفظة الافتراضية"""
        return self.wallets.get(user_id, {}).get('balance', 0.0)
    
    def transfer_to_trading(self, user_id, amount):
        """تحويل الأموال من المحفظة الافتراضية للتداول"""
        with self.lock:
            if self.wallets[user_id]['balance'] >= amount:
                self.wallets[user_id]['balance'] -= amount
                wallet_logger.info(f"Transferred {amount} USDT to trading for user {user_id}")
                return True
            wallet_logger.warning(f"Insufficient balance for user {user_id}")
            return False

# إنشاء كائن المحفظة الافتراضية وتصديره
wallet_instance = VirtualWallet()

# التصدير الصحيح للاستيراد في ملفات أخرى
def get_virtual_wallet():
    return wallet_instance

virtual_wallet = get_virtual_wallet()
