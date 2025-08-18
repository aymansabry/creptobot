from .abstract_exchange import AbstractExchange
import ccxt

class BinanceExchange(AbstractExchange):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret)
        self.fee = 0.001  # Binance trading fee

    def connect(self):
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'options': {
                'adjustForTimeDifference': True
            },
            'enableRateLimit': True
        })
        return self.exchange

    def validate_credentials(self):
        try:
            self.connect()
            balance = self.fetch_balance()
            return isinstance(balance, dict)
        except Exception as e:
            print(f"Binance validation error: {str(e)}")
            return False