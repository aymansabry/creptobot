from binance.client import Client
from binance.exceptions import BinanceAPIException
from user_manager import UserManager
from config import Config
import logging
import time

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_manager = UserManager()
        self.client = None
        self.trade_percent = Config.TRADE_PERCENT
        
    def initialize_client(self):
        credentials = self.user_manager.get_user_credentials(self.user_id)
        if not credentials or not credentials['is_active']:
            logger.error(f"User {self.user_id} not authorized for trading")
            return False
            
        try:
            self.client = Client(
                api_key=credentials['api_key'],
                api_secret=credentials['secret_key']
            )
            self.trade_percent = credentials['trade_percent']
            return True
        except Exception as e:
            logger.error(f"Failed to initialize client for user {self.user_id}: {str(e)}")
            return False
    
    def calculate_investment_amount(self, balance):
        amount = balance * (self.trade_percent / 100)
        return max(
            min(amount, Config.MAX_INVEST_AMOUNT),
            Config.MIN_INVEST_AMOUNT
        )
    
    def execute_order(self, symbol, side, usdt_balance):
        if not self.client and not self.initialize_client():
            return None
            
        amount = self.calculate_investment_amount(usdt_balance)
        
        for attempt in range(3):
            try:
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quoteOrderQty=amount  # For precise amount in USDT
                )
                logger.info(f"Order executed for user {self.user_id}: {order}")
                return order
            except BinanceAPIException as e:
                logger.warning(f"Attempt {attempt + 1} failed for user {self.user_id}: {str(e)}")
                if attempt == 2:
                    raise
                time.sleep(1)