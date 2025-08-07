import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from config import BINANCE_API_KEY, BINANCE_API_SECRET
from logger import logger

BASE_URL = "https://api.binance.com"

def get_headers():
    return {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

def sign_payload(payload):
    query_string = urlencode(payload)
    signature = hmac.new(BINANCE_API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return f"{query_string}&signature={signature}"

def place_order(symbol, side, quantity, price=None):
    url = f"{BASE_URL}/api/v3/order"
    timestamp = int(time.time() * 1000)
    payload = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": timestamp
    }
    signed = sign_payload(payload)
    response = requests.post(f"{url}?{signed}", headers=get_headers())
    data = response.json()
    logger.info(f"Binance Order Response: {data}")
    return data

def get_balance(asset="USDT"):
    url = f"{BASE_URL}/api/v3/account"
    timestamp = int(time.time() * 1000)
    query = sign_payload({"timestamp": timestamp})
    res = requests.get(f"{url}?{query}", headers=get_headers())
    balances = res.json().get("balances", [])
    for b in balances:
        if b["asset"] == asset:
            return float(b["free"])
    return 0.0
