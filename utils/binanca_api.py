import requests
import random

class BinanceAPI:
    def __init__(self, api_key=None, api_secret=None, test_mode=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.test_mode = test_mode

    def get_price(self, symbol):
        if self.test_mode:
            return round(random.uniform(100, 200), 2)
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        return float(response.json()['price'])

    def execute_trade(self, symbol, amount, side):
        if self.test_mode:
            price = self.get_price(symbol)
            print(f"[TEST] Executed {side} {amount} of {symbol} at {price}")
            return {"price": price, "status": "success"}
        # هنا ممكن تضيف تنفيذ فعلي باستخدام Binance SDK أو REST API
        raise NotImplementedError("التنفيذ الحقيقي غير مفعل حالياً")
