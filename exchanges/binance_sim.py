from .abstract_exchange import AbstractExchange
import random

class BinanceSimExchange(AbstractExchange):
    def __init__(self):
        self.balances = {'USDT': 10000.0}
        self.trade_history = []
    
    def get_balance(self, currency: str) -> float:
        return self.balances.get(currency, 0.0)
    
    def execute_trade(self, pair: str, amount: float, is_buy: bool) -> dict:
        profit = amount * random.uniform(0.01, 0.05)
        self.balances['USDT'] += profit if is_buy else -profit
        return {
            'status': 'FILLED',
            'executedQty': str(amount),
            'cummulativeQuoteQty': str(amount + profit)
        }
