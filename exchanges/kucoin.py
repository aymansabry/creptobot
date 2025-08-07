from kucoin.client import Client as KucoinClient
from core.config import config

class KuCoinAPI:
    def __init__(self):
        self.client = KucoinClient(
            config.KUCOIN_API_KEY,
            config.KUCOIN_API_SECRET,
            config.KUCOIN_API_PASSPHRASE
        )
    
    async def get_market_data(self, symbol: str):
        return self.client.get_ticker(symbol)
