import time
import hmac
import hashlib
import urllib.parse
import base64
import json
import asyncio
import httpx
from datetime import datetime
from db import update_user_balance, fetch_live_users, mark_user_stopped
from security import decrypt_api_key

ARBITRAGE_THRESHOLD = 0.005  # 0.5%
CHECK_INTERVAL = 10  # seconds
MAX_DRAWDOWN_PERCENT = 0.02  # 2% max loss

BINANCE_BASE_URL = "https://api.binance.com"
KUCOIN_BASE_URL = "https://api.kucoin.com"

def binance_sign(params: dict, secret: str) -> str:
    query_string = urllib.parse.urlencode(params)
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def kucoin_sign(api_secret: str, method: str, endpoint: str, body: str, timestamp: str) -> str:
    str_to_sign = f"{timestamp}{method.upper()}{endpoint}{body}"
    hmac_obj = hmac.new(api_secret.encode(), str_to_sign.encode(), hashlib.sha256)
    return base64.b64encode(hmac_obj.digest()).decode()

async def binance_market_order(api_key, secret_key, side, symbol, quantity):
    endpoint = "/api/v3/order"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": timestamp,
        "recvWindow": 5000
    }
    params["signature"] = binance_sign(params, secret_key)
    headers = {"X-MBX-APIKEY": api_key}
    async with httpx.AsyncClient() as client:
        resp = await client.post(BINANCE_BASE_URL + endpoint, params=params, headers=headers)
        return resp.json()

async def kucoin_market_order_create(api_key, api_secret, api_passphrase, side, symbol, size):
    endpoint = "/api/v1/orders"
    method = "POST"
    body = {
        "symbol": symbol,
        "side": side.lower(),
        "type": "market",
        "size": str(size)
    }
    timestamp = str(int(time.time() * 1000))
    body_json = json.dumps(body)
    signature = kucoin_sign(api_secret, method, endpoint, body_json, timestamp)
    headers = {
        "KC-API-KEY": api_key,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": api_passphrase,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(KUCOIN_BASE_URL + endpoint, headers=headers, data=body_json)
        return resp.json()

async def cancel_open_orders_binance(api_key, secret_key, symbol="BTCUSDT"):
    endpoint = "/api/v3/openOrders"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "timestamp": timestamp,
        "recvWindow": 5000
    }
    params["signature"] = binance_sign(params, secret_key)
    headers = {"X-MBX-APIKEY": api_key}
    async with httpx.AsyncClient() as client:
        r = await client.get(BINANCE_BASE_URL + endpoint, params=params, headers=headers)
        orders = r.json()
        if isinstance(orders, list):
            for order in orders:
                cancel_endpoint = "/api/v3/order"
                cancel_params = {
                    "symbol": symbol,
                    "orderId": order['orderId'],
                    "timestamp": int(time.time() * 1000),
                    "recvWindow": 5000
                }
                cancel_params["signature"] = binance_sign(cancel_params, secret_key)
                await client.delete(BINANCE_BASE_URL + cancel_endpoint, params=cancel_params, headers=headers)

async def cancel_open_orders_kucoin(api_key, api_secret, api_passphrase, symbol="BTC-USDT"):
    endpoint = f"/api/v1/orders?symbol={symbol}&status=active"
    method = "GET"
    timestamp = str(int(time.time() * 1000))
    body = ""
    signature = kucoin_sign(api_secret, method, endpoint, body, timestamp)
    headers = {
        "KC-API-KEY": api_key,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": timestamp,
        "KC-API-PASSPHRASE": api_passphrase,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(KUCOIN_BASE_URL + endpoint, headers=headers)
        data = resp.json()
        if data.get("code") == "200000":
            orders = data.get("data", [])
            for order in orders:
                cancel_endpoint = f"/api/v1/orders/{order['id']}"
                cancel_method = "DELETE"
                cancel_timestamp = str(int(time.time() * 1000))
                cancel_body = ""
                cancel_signature = kucoin_sign(api_secret, cancel_method, cancel_endpoint, cancel_body, cancel_timestamp)
                cancel_headers = {
                    "KC-API-KEY": api_key,
                    "KC-API-SIGN": cancel_signature,
                    "KC-API-TIMESTAMP": cancel_timestamp,
                    "KC-API-PASSPHRASE": api_passphrase,
                    "Content-Type": "application/json"
                }
                await client.delete(KUCOIN_BASE_URL + cancel_endpoint, headers=cancel_headers)

async def send_telegram_message(bot, user_id, text):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"Failed to send message to {user_id}: {e}")

async def check_stop_loss(user_data, bot):
    investment = user_data['investment_amount']
    total_pnl = user_data.get('total_profit_loss', 0)
    if total_pnl / investment < -MAX_DRAWDOWN_PERCENT:
        await send_telegram_message(bot, user_data['telegram_id'], 
            "⚠️ تم إيقاف التداول تلقائيًا بسبب تجاوز حد الخسارة المسموح به.")
        # يمكن هنا تحديث حالة المستخدم في DB لمنع التداول
        return True
    return False

async def arbitrage_for_user(bot, user_data):
    if await check_stop_loss(user_data, bot):
        return

    binance_price = await get_binance_price()
    kucoin_price = await get_kucoin_price()
    diff = (binance_price - kucoin_price) / kucoin_price

    print(f"{datetime.now()} | User {user_data['telegram_id']} | Binance: {binance_price}, KuCoin: {kucoin_price}, Diff: {diff:.4f}")

    qty = user_data['investment_amount'] / min(binance_price, kucoin_price)

    # فك تشفير مفاتيح API
    binance_api_key = decrypt_api_key(user_data['binance_api_key'])
    binance_secret_key = decrypt_api_key(user_data['binance_secret_key'])
    kucoin_api_key = decrypt_api_key(user_data['kucoin_api_key'])
    kucoin_secret_key = decrypt_api_key(user_data['kucoin_secret_key'])
    kucoin_passphrase = decrypt_api_key(user_data['kucoin_passphrase'])

    if diff > ARBITRAGE_THRESHOLD:
        buy_resp = await kucoin_market_order_create(
            kucoin_api_key, kucoin_secret_key, kucoin_passphrase,
            'buy', 'BTC-USDT', qty
        )
        sell_resp = await binance_market_order(
            binance_api_key, binance_secret_key, 'SELL', 'BTCUSDT', qty
        )
        profit_loss = (binance_price - kucoin_price) * qty
        await update_user_balance(user_data['telegram_id'], profit_loss)
        await send_telegram_message(bot, user_data['telegram_id'], f"تم تنفيذ مراجحة: شراء من KuCoin وبيع في Binance\\nالربح المتوقع: {profit_loss:.6f} USD")

    elif diff < -ARBITRAGE_THRESHOLD:
        buy_resp = await binance_market_order(
            binance_api_key, binance_secret_key, 'BUY', 'BTCUSDT', qty
        )
        sell_resp = await kucoin_market_order_create(
            kucoin_api_key, kucoin_secret_key, kucoin_passphrase,
            'sell', 'BTC-USDT', qty
        )
        profit_loss = (kucoin_price - binance_price) * qty
        await update_user_balance(user_data['telegram_id'], profit_loss)
        await send_telegram_message(bot, user_data['telegram_id'], f"تم تنفيذ مراجحة: شراء من Binance وبيع في KuCoin\\nالربح المتوقع: {profit_loss:.6f} USD")

    else:
        print("لا توجد فرصة مراجحة مناسبة الآن.")

    await cancel_open_orders_binance(binance_api_key, binance_secret_key)
    await cancel_open_orders_kucoin(kucoin_api_key, kucoin_secret_key, kucoin_passphrase)

async def arbitrage_loop_all_users(bot):
    while True:
        users = await fetch_live_users()
        tasks = [arbitrage_for_user(bot, user) for user in users]
        await asyncio.gather(*tasks)
        await asyncio.sleep(CHECK_INTERVAL)

async def get_binance_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
        return float(data['price'])

async def get_kucoin_price():
    url = "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
        return float(data['data']['price'])
