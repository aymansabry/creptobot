# utils/binance_utils.py

import aiohttp
from config.config import Config

HEADERS = {
    "X-MBX-APIKEY": Config.BINANCE_API_KEY
}

async def get_binance_deposit_tx(asset="USDT", limit=10):
    url = f"https://api.binance.com/sapi/v1/capital/deposit/hisrec"
    params = {"coin": asset, "limit": limit}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, params=params) as resp:
            return await resp.json()

async def get_wallet_balance():
    url = "https://api.binance.com/sapi/v3/asset/getUserAsset"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=HEADERS) as resp:
            return await resp.json()
