# project_root/services/trade_executor.py

import ccxt
from core.config import settings

class TradeExecutor:
    """
    Interacts with real exchanges using the CCXT library.
    """
    def __init__(self):
        self.exchanges = {
            'binance': ccxt.binance({
                'apiKey': settings.BINANCE_API_KEY,
                'secret': settings.BINANCE_SECRET_KEY,
                'options': {
                    'defaultType': 'spot',
                }
            }),
            'kucoin': ccxt.kucoin({
                'apiKey': settings.KUCOIN_API_KEY,
                'secret': settings.KUCOIN_SECRET_KEY,
                'password': settings.KUCOIN_PASSPHRASE,
                'options': {
                    'defaultType': 'spot',
                }
            })
        }

    async def get_ticker_price(self, exchange_name: str, symbol: str):
        """Fetches a real-time ticker price from the specified exchange."""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            print(f"Error: Exchange '{exchange_name}' not supported.")
            return None
            
        try:
            ticker = await exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'last': ticker['last']
            }
        except Exception as e:
            print(f"Error fetching ticker price from {exchange_name} for {symbol}: {e}")
            return None

    async def execute_order(self, exchange_name: str, symbol: str, type: str, side: str, amount: float):
        """Executes a real buy or sell order on the specified exchange."""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            print(f"Error: Exchange '{exchange_name}' not supported.")
            return None
            
        try:
            order = await exchange.create_order(symbol, type, side, amount)
            print(f"Real order placed on {exchange_name}: {order}")
            return order
        except Exception as e:
            print(f"Error executing order on {exchange_name}: {e}")
            return None
