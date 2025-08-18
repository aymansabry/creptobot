# /app/core/exchanges/coinbase.py
from .abstract_exchange import AbstractExchange
import ccxt

class CoinbaseExchange(AbstractExchange):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret)
        self.fee = 0.005  # رسوم كوين بيس الافتراضية

    def connect(self):
        self.exchange = ccxt.coinbase({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True
        })
        return self.exchange

    def validate_credentials(self):
        try:
            self.connect()
            balance = self.fetch_balance()
            return isinstance(balance, dict)
        except Exception as e:
            print(f"Coinbase validation error: {str(e)}")
            return False