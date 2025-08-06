from abc import ABC, abstractmethod

class AbstractExchange(ABC):
    @abstractmethod
    def get_balance(self, currency: str) -> float:
        pass
    
    @abstractmethod
    def execute_trade(self, pair: str, amount: float, is_buy: bool) -> dict:
        pass
