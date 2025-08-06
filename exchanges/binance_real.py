from .abstract_exchange import AbstractExchange
from binance.client import Client
import os

class BinanceRealExchange(AbstractExchange):
    def __init__(self):
        self.client = Client(
            api_key=os.getenv("BINANCE_API_KEY"),
            api_secret=os.getenv("BINANCE_API_SECRET")
        )
    
    def get_balance(self, currency: str) -> float:
        balance = self.client.get_asset_balance(asset=currency)
        return float(balance['free'])
    
    def execute_trade(self, pair: str, amount: float, is_buy: bool) -> dict:
        order = self.client.create_order(
            symbol=pair,
            side=Client.SIDE_BUY if is_buy else Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=amount
        )
        return order
