import time
import hashlib
import hmac
import base64
import requests
from core.config import KUCOIN_API_KEY, KUCOIN_API_SECRET, KUCOIN_API_PASSPHRASE

BASE_URL = "https://api.kucoin.com"

class KuCoinAPI:
    def __init__(self):
        self.api_key = KUCOIN_API_KEY
        self.api_secret = KUCOIN_API_SECRET
        self.api_passphrase = KUCOIN_API_PASSPHRASE

    def _sign(self, method, endpoint, body="", timestamp=""):
        str_to_sign = f"{timestamp}{method}{endpoint}{body}"
        signature = base64.b64encode(hmac.new(
            self.api_secret.encode(),
            str_to_sign.encode(),
            hashlib.sha256).digest())
        return signature.decode()

    def _headers(self, method, endpoint, body=""):
        timestamp = str(int(time.time() * 1000))
        signature = self._sign(method, endpoint, body, timestamp)
        return {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": self.api_passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }

    def get_account(self):
        endpoint = "/api/v1/accounts"
        headers = self._headers("GET", endpoint)
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def place_order(self, symbol, side, size, order_type="market"):
        endpoint = "/api/v1/orders"
        import json
        body = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "size": size
        }
        body_json = json.dumps(body)
        headers = self._headers("POST", endpoint, body_json)
        url = f"{BASE_URL}{endpoint}"
        resp = requests.post(url, headers=headers, data=body_json)
        resp.raise_for_status()
        return resp.json()
