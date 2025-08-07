from datetime import datetime
from db.crud import update_wallet_balance

class WalletTracker:
    @staticmethod
    def record_transaction(user_id: str, amount: float, currency: str):
        update_wallet_balance(
            user_id=user_id,
            amount=amount,
            currency=currency,
            timestamp=datetime.now()
        )
