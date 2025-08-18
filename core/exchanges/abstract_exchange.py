import ccxt
from abc import ABC, abstractmethod

class AbstractExchange(ABC):
    def __init__(self, api_key: str, api_secret: str):
        self.exchange = None
        self.api_key = api_key
        self.api_secret = api_secret
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def validate_credentials(self):
        pass
    
    def fetch_balance(self):
        return self.exchange.fetch_balance()
    
    def fetch_order_book(self, symbol: str):
        return self.exchange.fetch_order_book(symbol)