from utils.logger import exchange_logger, log_error
from binance.client import Client
from binance.exceptions import BinanceAPIException
from core.config import config
import time

class BinanceAPI:
    def __init__(self):
        self.client = Client(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
        self.logger = exchange_logger
        self.min_order_size = {
            'BTCUSDT': 0.00001,
            'ETHUSDT': 0.001,
            'BNBUSDT': 0.01
        }

    async def check_balance(self, symbol, required_amount):
        """التحقق من الرصيد المتاح"""
        base_asset = symbol.replace('USDT', '')
        try:
            balance = self.client.get_asset_balance(asset=base_asset)
            free_balance = float(balance['free'])
            
            if free_balance >= required_amount:
                return True
            return False
        except BinanceAPIException as e:
            log_error(f"Balance check failed: {str(e)}")
            return False

    async def execute_order(self, symbol, side, quantity):
        """تنفيذ الأمر مع إدارة الرصيد الذكية"""
        try:
            # التحقق من الحد الأدنى لحجم الطلب
            min_size = self.min_order_size.get(symbol, 0.001)
            if quantity < min_size:
                raise ValueError(f"Quantity below minimum order size ({min_size})")

            # التحقق من الرصيد قبل التنفيذ
            if side == 'BUY':
                usdt_balance = float(self.client.get_asset_balance(asset='USDT')['free'])
                current_price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
                required_usdt = quantity * current_price
                
                if usdt_balance < required_usdt:
                    raise ValueError(f"Insufficient USDT balance. Available: {usdt_balance}, Required: {required_usdt}")
            else:
                if not await self.check_balance(symbol, quantity):
                    asset = symbol.replace('USDT', '')
                    balance = self.client.get_asset_balance(asset=asset)
                    raise ValueError(f"Insufficient {asset} balance. Available: {balance['free']}, Required: {quantity}")

            # تنفيذ الأمر
            self.logger.info(f"Executing {side} order for {quantity} {symbol}")
            
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            self.logger.info(f"Order executed: {order}")
            return order
            
        except BinanceAPIException as e:
            log_error(f"Binance API Error: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            log_error(f"Order execution error: {str(e)}")
            raise
