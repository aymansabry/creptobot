from binance.client import Client
from core.config import config
from utils.logger import exchange_logger

class BinanceAPI:
    def __init__(self):
        self.client = Client(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
    
    async def execute_arbitrage(self, trade_data: dict):
        try:
            # تنفيذ صفقة الشراء
            buy_order = self.client.create_order(
                symbol=trade_data['buy_pair'],
                side='BUY',
                type='MARKET',
                quantity=trade_data['amount']
            )
            
            # تنفيذ صفقة البيع
            sell_order = self.client.create_order(
                symbol=trade_data['sell_pair'],
                side='SELL',
                type='MARKET',
                quantity=trade_data['amount']
            )
            
            return {
                'status': 'completed',
                'buy_order': buy_order,
                'sell_order': sell_order
            }
        except Exception as e:
            exchange_logger.error(f"Binance error: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
