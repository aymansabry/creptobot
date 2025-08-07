from exchanges.binance import BinanceAPI
from utils.logger import trade_logger, log_error

class TradingEngine:
    def __init__(self):
        self.api = BinanceAPI()
        trade_logger.info("Trading engine initialized")

    async def execute_trade(self, pair, amount):
        try:
            trade_logger.info(f"Starting trade for {pair} with {amount} USDT")
            
            # تنفيذ الصفقة
            buy_order = await self.api.execute_order(pair, 'BUY', amount)
            sell_order = await self.api.execute_order(pair, 'SELL', amount)
            
            trade_logger.info(f"Trade completed successfully")
            return {
                'status': 'completed',
                'buy_order': buy_order,
                'sell_order': sell_order
            }
            
        except Exception as e:
            log_error(f"Trade failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
