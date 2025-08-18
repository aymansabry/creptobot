import hmac
import hashlib
import urllib.parse
import aiohttp
import asyncio
from typing import Dict, List, Optional
from decimal import Decimal
from core.utilities import Logger

logger = Logger(__name__)

class Binance:
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.api_secret = config['api_secret']
        self.base_url = "https://api.binance.com"
        self.websocket_url = "wss://stream.binance.com:9443/ws"
        self.session = aiohttp.ClientSession()
        self.headers = {
            'X-MBX-APIKEY': self.api_key
        }

    def _generate_signature(self, params: dict) -> str:
        """توليد توقيع API"""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def get_order_book(self, symbol: str, limit: int = 5) -> Optional[Dict]:
        """الحصول على سجل الطلبات لزوج تداول"""
        try:
            endpoint = "/api/v3/depth"
            params = {
                'symbol': symbol.replace('/', ''),
                'limit': limit
            }
            
            async with self.session.get(
                self.base_url + endpoint,
                params=params,
                headers=self.headers
            ) as response:
                data = await response.json()
                
                if 'bids' not in data or 'asks' not in data:
                    logger.warning(f"Invalid order book data for {symbol}")
                    return None
                
                return {
                    'bids': [[Decimal(price), Decimal(quantity)] for price, quantity in data['bids']],
                    'asks': [[Decimal(price), Decimal(quantity)] for price, quantity in data['asks']]
                }
                
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return None

    async def create_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict:
        """إنشاء أمر تداول"""
        try:
            endpoint = "/api/v3/order"
            params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': 'LIMIT' if price else 'MARKET',
                'quantity': round(amount, 6),
                'timestamp': int(time.time() * 1000),
                'recvWindow': 5000
            }
            
            if price:
                params['price'] = str(round(price, 6))
                params['timeInForce'] = 'GTC'
            
            params['signature'] = self._generate_signature(params)
            
            async with self.session.post(
                self.base_url + endpoint,
                params=params,
                headers=self.headers
            ) as response:
                data = await response.json()
                
                if 'status' in data and data['status'] == 'FILLED':
                    logger.info(f"Order executed: {data}")
                    return {
                        'status': 'success',
                        'orderId': data['orderId'],
                        'executedQty': Decimal(data['executedQty']),
                        'avgPrice': Decimal(data['avgPrice'])
                    }
                else:
                    logger.warning(f"Order not filled: {data}")
                    return {
                        'status': 'error',
                        'message': data.get('msg', 'Unknown error')
                    }
                    
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    async def get_account_balance(self) -> Dict[str, Decimal]:
        """الحصول على أرصدة الحساب"""
        try:
            endpoint = "/api/v3/account"
            params = {
                'timestamp': int(time.time() * 1000)
            }
            params['signature'] = self._generate_signature(params)
            
            async with self.session.get(
                self.base_url + endpoint,
                params=params,
                headers=self.headers
            ) as response:
                data = await response.json()
                return {
                    asset['asset']: Decimal(asset['free'])
                    for asset in data['balances']
                    if Decimal(asset['free']) > 0
                }
                
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
            return {}

    async def close(self):
        """إغلاق الجلسة"""
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()