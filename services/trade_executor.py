# project_root/services/trade_executor.py

import ccxt.async_support as ccxt
from core.config import settings

class TradeExecutor:
    """
    Executes trading orders on various exchanges.
    """
    def __init__(self):
        self.binance_client = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_SECRET_KEY,
            'options': {
                'defaultType': 'spot',
            },
        })
        self.kucoin_client = ccxt.kucoin({
            'apiKey': settings.KUCOIN_API_KEY,
            'secret': settings.KUCOIN_SECRET_KEY,
            'password': settings.KUCOIN_PASS_PHRASE,
        })
        self.clients = {
            'binance': self.binance_client,
            'kucoin': self.kucoin_client,
        }

    async def execute_order(self, exchange: str, symbol: str, type: str, side: str, amount: float):
        """
        Submits a buy/sell order to a specified exchange.
        """
        client = self.clients.get(exchange)
        if not client:
            raise ValueError(f"Unsupported exchange: {exchange}")

        try:
            order = await client.create_order(
                symbol=symbol,
                type=type,
                side=side,
                amount=amount,
            )
            return order
        except Exception as e:
            print(f"Error executing order on {exchange}: {e}")
            return None

    async def fetch_balance(self, exchange: str, currency: str):
        """
        Fetches the balance of a specific currency from an exchange.
        """
        client = self.clients.get(exchange)
        if not client:
            raise ValueError(f"Unsupported exchange: {exchange}")
        
        balance = await client.fetch_balance()
        return balance[currency]

    async def close(self):
        """
        Closes all exchange connections.
        """
        await self.binance_client.close()
        await self.kucoin_client.close()
