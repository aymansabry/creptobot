from exchange.binance_client import BinanceClient
from config import settings

class Market:
    def __init__(self, client: BinanceClient):
        self.client = client
        self.markets = self.client.load_markets()

    def refresh(self):
        self.markets = self.client.load_markets()

    def list_supported_symbols(self):
        return list(self.markets.keys())

    def symbol_info(self, symbol: str):
        return self.markets.get(symbol)

    def best_price(self, symbol: str, is_buy: bool):
        book = self.client.fetch_order_book(symbol, limit=5)
        if not book:
            return None
        return book['asks'][0][0] if is_buy else book['bids'][0][0]
