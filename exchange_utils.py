# exchange_utils.py
import httpx
import time, hmac, hashlib, base64

async def validate_binance(api_key: str, api_secret: str) -> bool:
    # نجرّب endpoint يتطلب المفتاح. هذا تحقق بسيط — في production حسن التوقيع.
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            headers = {"X-MBX-APIKEY": api_key}
            r = await client.get("https://api.binance.com/api/v3/account", headers=headers)
            return r.status_code == 200
    except Exception:
        return False

async def validate_kucoin(api_key: str, api_secret: str, passphrase: str) -> bool:
    try:
        endpoint = "/api/v1/accounts"
        timestamp = str(int(time.time() * 1000))
        method = "GET"
        str_to_sign = timestamp + method + endpoint
        signature = base64.b64encode(hmac.new(api_secret.encode(), str_to_sign.encode(), hashlib.sha256).digest()).decode()
        headers = {
            "KC-API-KEY": api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": passphrase,
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get("https://api.kucoin.com" + endpoint, headers=headers)
            if r.status_code == 200:
                data = r.json()
                return data.get("code") == "200000" or True
            return False
    except Exception:
        return False
