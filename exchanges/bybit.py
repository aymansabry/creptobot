from pybit import HTTP
from core.config import config

class BybitAPI:
    def __init__(self):
        self.session = HTTP(
            endpoint="https://api.bybit.com",
            api_key=config.BYBIT_API_KEY,
            api_secret=config.BYBIT_API_SECRET
        )
    
    async def get_orderbook(self, symbol: str):
        return self.session.orderbook(symbol=symbol)
