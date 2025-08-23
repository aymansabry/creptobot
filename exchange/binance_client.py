import ccxt
from config import settings

class BinanceClient:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        self.x = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        if settings.binance_testnet:
            try:
                self.x.set_sandbox_mode(True)
            except Exception:
                pass

    def load_markets(self):
        return self.x.load_markets()

    def fetch_order_book(self, symbol: str, limit: int = 10):
        return self.x.fetch_order_book(symbol, limit=limit)

    def fetch_ticker(self, symbol: str):
        return self.x.fetch_ticker(symbol)

    def fetch_balance(self):
        return self.x.fetch_balance()

    def create_market_order(self, symbol: str, side: str, amount: float):
        if not settings.live_mode:
            price = self.fetch_ticker(symbol)['last']
            return {"id": "paper", "symbol": symbol, "side": side, "amount": amount, "status": "filled", "price": price}
        return self.x.create_order(symbol=symbol, type='market', side=side, amount=amount)

    def withdraw(self, code: str, amount: float, address: str, params=None):
        if not settings.live_mode:
            return {"id": "paper-withdraw", "currency": code, "amount": amount, "address": address}
        return self.x.withdraw(code, amount, address, params or {})

    def markets(self):
        return self.x.markets
