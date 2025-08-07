from exchanges.binance import BinanceAPI
from utils.logger import trade_logger, log_error
import time

class TradingEngine:
    def __init__(self):
        self.api = BinanceAPI()
        trade_logger.info("Trading engine initialized")
        self.max_retries = 3
        self.retry_delay = 5  # ثواني

    async def execute_trade(self, pair, amount):
        """تنفيذ الصفقة مع إعادة المحاولة التلقائية"""
        for attempt in range(self.max_retries):
            try:
                trade_logger.info(f"Starting trade for {pair} with {amount} USDT (Attempt {attempt + 1})")
                
                # التحقق من الرصيد أولاً
                usdt_balance = float(self.api.client.get_asset_balance(asset='USDT')['free'])
                if usdt_balance < amount:
                    raise ValueError(f"Insufficient USDT balance. Available: {usdt_balance}, Required: {amount}")

                # تنفيذ الصفقة
                buy_order = await self.api.execute_order(pair, 'BUY', amount)
                
                # انتظار تنفيذ الأمر بالكامل
                time.sleep(2)
                
                # الحصول على الكمية المشتراة الفعلية
                executed_qty = float(buy_order['executedQty'])
                
                # تنفيذ أمر البيع بنفس الكمية المشتراة
                sell_order = await self.api.execute_order(pair, 'SELL', executed_qty)
                
                trade_logger.info(f"Trade completed successfully")
                return {
                    'status': 'completed',
                    'buy_order': buy_order,
                    'sell_order': sell_order,
                    'profit': self.calculate_profit(buy_order, sell_order)
                }
                
            except ValueError as e:
                log_error(f"Trade validation failed: {str(e)}")
                return {
                    'status': 'failed',
                    'error': str(e),
                    'retry': False
                }
            except Exception as e:
                log_error(f"Trade attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {
                        'status': 'failed',
                        'error': str(e),
                        'retry': False
                    }
                time.sleep(self.retry_delay)
                continue

    def calculate_profit(self, buy_order, sell_order):
        """حساب الربح الصافي"""
        buy_cost = sum(float(fill['price']) * float(fill['qty']) for fill in buy_order['fills'])
        sell_revenue = sum(float(fill['price']) * float(fill['qty']) for fill in sell_order['fills'])
        return sell_revenue - buy_cost
