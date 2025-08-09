import hmac
import hashlib
import time
import requests
from core.config import BINANCE_API_KEY, BINANCE_API_SECRET

BASE_URL = "https://api.binance.com"

class BinanceAPI:
    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET

    def _sign(self, params):
        query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    def _get(self, path, params=None):
        if params is None:
            params = {}
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{BASE_URL}{path}"
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_account_info(self):
        return self._get("/api/v3/account")

    def place_order(self, symbol, side, quantity, order_type="MARKET"):
        path = "/api/v3/order"
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type,
            "quantity": quantity,
            "timestamp": int(time.time() * 1000),
        }
        params['signature'] = self._sign(params)
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{BASE_URL}{path}"
        resp = requests.post(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()
