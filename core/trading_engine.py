from core.virtual_wallet import virtual_wallet

class TradingEngine:
    async def execute_trade(self, user_id, pair, amount):
        """تنفيذ الصفقة باستخدام الرصيد الافتراضي"""
        # التحقق من الرصيد الافتراضي أولاً
        if not virtual_wallet.transfer_to_trading(user_id, amount):
            raise ValueError(f"رصيد المحفظة غير كافي. الرصيد المتاح: {virtual_wallet.get_balance(user_id)} USDT")
        
        try:
            # ... باقي كود التنفيذ ...
            return {
                'status': 'completed',
                'profit': profit,
                'new_balance': virtual_wallet.get_balance(user_id)
            }
        except Exception as e:
            # استرجاع المبلغ في حالة الخطأ
            virtual_wallet.deposit(user_id, amount)
            raise
