from .abstract_exchange import AbstractExchange
import ccxt

class BinanceExchange(AbstractExchange):
    def connect(self):
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True
        })
        return self.exchange
    
    def validate_credentials(self):
        try:
            self.connect()
            balance = self.fetch_balance()
            return 'total' in balance
        except Exception:
            return False