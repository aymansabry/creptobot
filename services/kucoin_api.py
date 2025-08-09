from utils.encryption import EncryptionService

class ExchangeAPIManager:
    def __init__(self, user):
        self.exchanges = {}
        enc = EncryptionService()

        if user.encrypted_binance_api_key and user.encrypted_binance_api_secret:
            from services.binance_api import BinanceAPI
            binance_api_key = enc.decrypt(user.encrypted_binance_api_key)
            binance_api_secret = enc.decrypt(user.encrypted_binance_api_secret)
            self.exchanges["binance"] = BinanceAPI(binance_api_key, binance_api_secret)

        if user.encrypted_kucoin_api_key and user.encrypted_kucoin_api_secret and user.encrypted_kucoin_api_passphrase:
            from services.kucoin_api import KuCoinAPI
            kucoin_api_key = enc.decrypt(user.encrypted_kucoin_api_key)
            kucoin_api_secret = enc.decrypt(user.encrypted_kucoin_api_secret)
            kucoin_api_passphrase = enc.decrypt(user.encrypted_kucoin_api_passphrase)
            self.exchanges["kucoin"] = KuCoinAPI(kucoin_api_key, kucoin_api_secret, kucoin_api_passphrase)

    def get_exchange(self, name):
        return self.exchanges.get(name)

    def list_active_exchanges(self):
        return list(self.exchanges.keys())
