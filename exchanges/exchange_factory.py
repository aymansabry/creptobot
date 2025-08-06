from .abstract_exchange import AbstractExchange
from .binance_real import BinanceRealExchange
from .binance_sim import BinanceSimExchange
from core.config import SystemConfig

class ExchangeFactory:
    @staticmethod
    def create_exchange(wallet_type=None):
        if wallet_type == SystemConfig.OperationMode.REAL or (
            wallet_type is None and SystemConfig.CURRENT_MODE == SystemConfig.OperationMode.REAL
        ):
            return BinanceRealExchange()
        return BinanceSimExchange()
