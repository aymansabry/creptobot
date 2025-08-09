# binance_api.py
import hmac, hashlib, time, requests
from urllib.parse import urlencode

BASE = "https://api.binance.com"

class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.key = api_key
        self.secret = api_secret

    def _sign(self, params):
        q = urlencode(params)
        return hmac.new(self.secret.encode(), q.encode(), hashlib.sha256).hexdigest()

    def _headers(self):
        return {'X-MBX-APIKEY': self.key}

    def get_account_balance(self, asset='USDT'):
        path = "/api/v3/account"
        ts = int(time.time()*1000)
        params = {'timestamp': ts}
        params['signature'] = self._sign(params)
        r = requests.get(BASE+path, headers=self._headers(), params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        for b in data.get('balances', []):
            if b['asset'] == asset:
                return float(b['free'])
        return 0.0

    def get_symbol_price(self, symbol):
        r = requests.get(BASE + "/api/v3/ticker/price", params={'symbol': symbol}, timeout=5)
        r.raise_for_status()
        return float(r.json()['price'])

    def create_order_market(self, symbol, side, quantity):
        path = "/api/v3/order"
        ts = int(time.time()*1000)
        params = {'symbol': symbol, 'side': side, 'type': 'MARKET', 'quantity': quantity, 'timestamp': ts}
        params['signature'] = self._sign(params)
        r = requests.post(BASE + path, headers=self._headers(), params=params, timeout=10)
        return r.json()
