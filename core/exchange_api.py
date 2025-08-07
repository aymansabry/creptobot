import ccxt
from typing import Dict, Optional
import asyncio

class ExchangeAPI:
    def __init__(self, api_key: str, api_secret: str, exchange_name: str):
        self.exchange = getattr(ccxt, exchange_name)({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        
    async def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        try:
            if order_type == 'market':
                order = await self.exchange.create_order(symbol, order_type, side, amount)
            else:
                order = await self.exchange.create_order(symbol, order_type, side, amount, price)
            return order
        except Exception as e:
            raise Exception(f"Order failed: {str(e)}")
    
    async def get_balance(self, currency: str) -> float:
        try:
            balance = await self.exchange.fetch_balance()
            return balance['free'].get(currency.upper(), 0.0)
        except Exception as e:
            raise Exception(f"Failed to get balance: {str(e)}")
    
    async def withdraw(self, currency: str, amount: float, address: str, network: str = 'TRX') -> Dict:
        try:
            result = await self.exchange.withdraw(currency, amount, address, None, {'network': network})
            return result
        except Exception as e:
            raise Exception(f"Withdrawal failed: {str(e)}")
