from binance.spot import Spot
from config import config
import asyncio

client = Spot(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)

async def get_real_deals():
    prices = client.ticker_price()
    btc_price = float(next(p for p in prices if p['symbol'] == 'BTCUSDT')['price'])
    eth_price = float(next(p for p in prices if p['symbol'] == 'ETHUSDT')['price'])
    
    return [{
        'id': 1,
        'symbol': 'BTC/USDT',
        'price': btc_price,
        'profit': round((btc_price/eth_price - 1) * 100, 2)
    }]
