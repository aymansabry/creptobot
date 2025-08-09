# kucoin_api.py
import requests, time, hmac, hashlib, base64, json
from urllib.parse import urljoin

BASE = "https://api.kucoin.com"

class KucoinAPI:
    def __init__(self, api_key, api_secret, passphrase):
        self.key = api_key
        self.secret = api_secret
        self.passphrase = passphrase

    def _sign(self, method, endpoint, now, body=''):
        str_to_sign = str(now) + method + endpoint + body
        signature = base64.b64encode(hmac.new(self.secret.encode(), str_to_sign.encode(), hashlib.sha256).digest())).decode()
        return signature

    def _pass(self):
        return base64.b64encode(hmac.new(self.secret.encode(), self.passphrase.encode(), hashlib.sha256).digest()).decode()

    def _headers(self, method, endpoint, body=''):
        now = str(int(time.time()*1000))
        sig = self._sign(method, endpoint, now, body)
        headers = {
            "KC-API-KEY": self.key,
            "KC-API-SIGN": sig,
            "KC-API-TIMESTAMP": now,
            "KC-API-PASSPHRASE": self._pass(),
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }
        return headers

    def get_account_balance(self, currency='USDT'):
        endpoint = "/api/v1/accounts"
        r = requests.get(BASE+endpoint, headers=self._headers('GET', endpoint), timeout=10)
        r.raise_for_status()
        data = r.json().get('data', [])
        for acc in data:
            if acc['currency'] == currency and acc['type']=='trade':
                return float(acc['available'])
        return 0.0

    def get_symbol_price(self, symbol):
        r = requests.get(BASE + "/api/v1/market/orderbook/level1", params={'symbol': symbol}, timeout=5)
        r.raise_for_status()
        return float(r.json()['data']['price'])

    def create_order_market(self, symbol, side, size):
        endpoint = "/api/v1/orders"
        body = json.dumps({"clientOid": str(int(time.time()*1000)), "side": side, "symbol": symbol, "type": "market", "size": size})
        r = requests.post(BASE + endpoint, headers=self._headers('POST', endpoint, body), data=body, timeout=10)
        return r.json()
