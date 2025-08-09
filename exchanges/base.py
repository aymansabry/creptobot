import ccxt.pro as ccxt
import asyncio
from core.logger import get_logger
from decimal import Decimal

logger = get_logger('exchange.base')

class ExchangeWrapper:
    def __init__(self, name, api_key=None, secret=None, password=None):
        self.name = name.lower()
        if self.name not in ccxt.exchanges:
            raise ValueError(f'{self.name} not supported by ccxt')
        self.cls = getattr(ccxt, self.name)
        params = {}
        self.exchange = self.cls({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'enableRateLimit': True,
            **params
        })

    async def fetch_ticker(self, symbol):
        try:
            return await self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f'Failed to fetch ticker from {self.name} for {symbol}: {e}')
            return None

    async def fetch_balance(self):
        try:
            return await self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f'Failed to fetch balance from {self.name}: {e}')
            return None
            
    async def close(self):
        await self.exchange.close()
