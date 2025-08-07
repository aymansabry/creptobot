from utils.logger import exchange_logger, log_error
from binance.client import Client
from core.config import config

class BinanceAPI:
    def __init__(self):
        self.client = Client(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
        self.logger = exchange_logger

    async def execute_order(self, symbol, side, quantity):
        try:
            self.logger.info(f"Executing {side} order for {quantity} {symbol}")
            
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            self.logger.info(f"Order executed: {order}")
            return order
            
        except Exception as e:
            log_error(f"Binance API Error: {str(e)}", exc_info=True)
            raise
