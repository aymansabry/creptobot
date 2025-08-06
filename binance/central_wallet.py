from binance.client import Client
from core.config import Config
import logging

logger = logging.getLogger(__name__)

class CentralWallet:
    def __init__(self):
        self.client = Client(Config.BINANCE_API_KEY, Config.BINANCE_SECRET)
    
    def get_balance(self, asset='USDT') -> float:
        try:
            balance = float(self.client.get_asset_balance(asset)['free'])
            logger.info(f"Retrieved balance: {balance} {asset}")
            return balance
        except Exception as e:
            logger.error(f"Balance check failed: {str(e)}")
            return 0.0
    
    def get_all_balances(self) -> dict:
        assets = ['USDT', 'BTC', 'ETH', 'BNB']
        return {asset: self.get_balance(asset) for asset in assets}
