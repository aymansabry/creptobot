import aiohttp
import asyncio

BINANCE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=USDTUSDT"  # مثال فقط
KUCOIN_URL = "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=USDT-USDT"
BITFINEX_URL = "https://api-pub.bitfinex.com/v2/ticker/tUSTUSD"

async def fetch_binance():
    async with aiohttp.ClientSession() as session:
        async with session.get(BINANCE_URL) as resp:
            data = await resp.json()
            return float(data["price"])

async def fetch_kucoin():
    async with aiohttp.ClientSession() as session:
        async with session.get(KUCOIN_URL) as resp:
            data = await resp.json()
            return float(data["data"]["price"])

async def fetch_bitfinex():
    async with aiohttp.ClientSession() as session:
        async with session.get(BITFINEX_URL) as resp:
            data = await resp.json()
            return float(data[0])

async def fetch_all_prices():
    results = await asyncio.gather(
        fetch_binance(),
        fetch_kucoin(),
        fetch_bitfinex(),
        return_exceptions=True
    )
    return {
        "Binance": results[0],
        "KuCoin": results[1],
        "Bitfinex": results[2]
    }
