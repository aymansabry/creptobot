import ccxt
from config import Config
from typing import Optional, Dict, Any

class ExchangeAPI:
    def __init__(self, platform: str):
        self.platform = platform
        self.cipher = Config.CIPHER
    
    def encrypt_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def validate_credentials(self, api_key: str, api_secret: str, passphrase: Optional[str] = None) -> bool:
        try:
            exchange_class = getattr(ccxt, self.platform)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'password': passphrase if passphrase else None,
                'enableRateLimit': True
            })
            exchange.fetch_balance()  # اختبار الاتصال
            return True
        except Exception as e:
            print(f"{self.platform.upper()} API Error: {e}")
            return False
    
    def get_ticker_price(self, symbol: str, credentials: Dict[str, Any]) -> Optional[float]:
        try:
            exchange_class = getattr(ccxt, self.platform)
            exchange = exchange_class({
                'apiKey': self.decrypt_data(credentials['api_key']),
                'secret': self.decrypt_data(credentials['api_secret']),
                'password': self.decrypt_data(credentials['passphrase']) if 'passphrase' in credentials else None,
                'enableRateLimit': True
            })
            ticker = exchange.fetch_ticker(symbol)
            return ticker['bid'] if 'bid' in ticker else None
        except Exception as e:
            print(f"Error fetching {symbol} price from {self.platform}: {e}")
            return None

class BinanceAPI(ExchangeAPI):
    def __init__(self):
        super().__init__('binance')

class KuCoinAPI(ExchangeAPI):
    def __init__(self):
        super().__init__('kucoin')
