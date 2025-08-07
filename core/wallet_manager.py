from typing import Dict, List
from db.crud import get_user_wallet, update_wallet_balance
from db.models import Wallet
import uuid

class WalletManager:
    @staticmethod
    async def create_virtual_wallet(user_id: int, currencies: List[str]) -> Dict:
        wallet_data = {
            'user_id': user_id,
            'address': str(uuid.uuid4()),
            'balances': {currency: 0.0 for currency in currencies}
        }
        wallet = await Wallet.create(**wallet_data)
        return wallet
    
    @staticmethod
    async def deposit_to_wallet(user_id: int, currency: str, amount: float) -> Dict:
        wallet = await get_user_wallet(user_id)
        if not wallet:
            raise ValueError("Wallet not found")
        
        wallet.balances[currency] = wallet.balances.get(currency, 0.0) + amount
        await wallet.save()
        
        return {
            'status': 'success',
            'new_balance': wallet.balances[currency],
            'currency': currency
        }
    
    @staticmethod
    async def withdraw_from_wallet(user_id: int, currency: str, amount: float, to_address: str) -> Dict:
        wallet = await get_user_wallet(user_id)
        if not wallet:
            raise ValueError("Wallet not found")
        
        if wallet.balances.get(currency, 0.0) < amount:
            raise ValueError("Insufficient balance")
        
        wallet.balances[currency] -= amount
        await wallet.save()
        
        return {
            'status': 'success',
            'transaction_id': str(uuid.uuid4()),
            'amount': amount,
            'currency': currency,
            'to_address': to_address
        }
    
    @staticmethod
    async def transfer_to_main_wallet(user_id: int, amount: float, currency: str = 'USDT') -> Dict:
        # تحويل العمولة إلى محفظة المالك
        owner_wallet = await get_user_wallet(0)  # محفظة المالك لها user_id = 0
        user_wallet = await get_user_wallet(user_id)
        
        if user_wallet.balances.get(currency, 0.0) < amount:
            raise ValueError("Insufficient balance")
        
        # خصم من محفظة المستخدم
        user_wallet.balances[currency] -= amount
        await user_wallet.save()
        
        # إضافة إلى محفظة المالك
        owner_wallet.balances[currency] = owner_wallet.balances.get(currency, 0.0) + amount
        await owner_wallet.save()
        
        return {
            'status': 'success',
            'amount': amount,
            'currency': currency,
            'user_new_balance': user_wallet.balances[currency],
            'owner_new_balance': owner_wallet.balances[currency]
        }
