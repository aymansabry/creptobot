# core/trade_executor.py

class TradeExecutor:
    def __init__(self, binance_api, main_wallet_address=None):
        self.binance_api = binance_api
        self.main_wallet_address = main_wallet_address
        self.active_users = set()

    def enable_trading_for_user(self, user_id: int):
        self.active_users.add(user_id)

    def disable_trading_for_user(self, user_id: int):
        self.active_users.discard(user_id)

    def is_user_active(self, user_id: int) -> bool:
        return user_id in self.active_users

    async def execute_trade_for_user(self, user_id: int):
        if not self.is_user_active(user_id):
            print(f"❌ المستخدم {user_id} غير مفعل للتداول.")
            return

        # تنفيذ الصفقة التجريبية أو الحقيقية
        print(f"🚀 تنفيذ صفقة للمستخدم {user_id}")

        # مثال وهمي - استبدله بالتنفيذ الحقيقي
        trade_result = {
            "status": "success",
            "symbol": "BTC/USDT",
            "amount": 0.01,
            "price": 29000
        }

        return trade_result