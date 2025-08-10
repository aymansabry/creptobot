import ccxt
from utils import decrypt_text

class CCXTClientFactory:
    @staticmethod
    def create(exchange_name: str, api_key_enc: str, api_secret_enc: str, passphrase_enc: str = None):
        api_key = decrypt_text(api_key_enc)
        api_secret = decrypt_text(api_secret_enc)
        passphrase = decrypt_text(passphrase_enc) if passphrase_enc else None

        exchange_name = exchange_name.lower()
        if exchange_name == 'binance':
            return ccxt.binance({ 'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True })
        elif exchange_name == 'bybit':
            return ccxt.bybit({ 'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True })
        elif exchange_name in ('okx','okex'):
            return ccxt.okx({ 'apiKey': api_key, 'secret': api_secret, 'password': passphrase, 'enableRateLimit': True })
        else:
            raise ValueError('Unsupported exchange: ' + exchange_name)
