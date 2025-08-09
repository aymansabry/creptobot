class ExchangeAPIManager:
    def __init__(self, config):
        self.exchanges = {}

        if config.get("BINANCE_ENABLED", False):
            from services.binance_api import BinanceAPI
            self.exchanges["binance"] = BinanceAPI()

        if config.get("KUCOIN_ENABLED", False):
            from services.kucoin_api import KuCoinAPI
            self.exchanges["kucoin"] = KuCoinAPI()

    def get_exchange(self, name):
        return self.exchanges.get(name)

    def list_active_exchanges(self):
        return list(self.exchanges.keys())
