from binance.spot import Spot
from config import config

class BinanceClient:
    def __init__(self):
        self.client = Spot(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_SECRET,
            base_url=config.BINANCE_API_URL
        )
    
    async def get_price(self, symbol: str):
        return self.client.ticker_price(symbol)
    
    async def create_order(self, **params):
        return self.client.new_order(**params)
