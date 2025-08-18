from core.exchanges import BinanceExchange, CoinbaseExchange
from config import Config

async def calculate_spatial_arbitrage(user_id: str, symbol: str, db):
    """
    حساب المراجحة المكانية بين منصتين
    """
    user_apis = db.get_exchange_apis(user_id)
    
    binance = BinanceExchange(user_apis['binance'])
    coinbase = CoinbaseExchange(user_apis['coinbase'])
    
    binance_ob = binance.fetch_order_book(symbol)
    coinbase_ob = coinbase.fetch_order_book(symbol)
    
    # حساب أفضل سعر مع الرسوم
    effective_buy = coinbase_ob['bids'][0][0] * (1 - coinbase.fee)
    effective_sell = binance_ob['asks'][0][0] * (1 + binance.fee)
    
    profit = effective_buy - effective_sell
    if profit > Config.MIN_PROFIT:
        return {
            'profit': profit,
            'volume': min(binance_ob['asks'][0][1], coinbase_ob['bids'][0][1]),
            'direction': 'binance -> coinbase',
            'symbol': symbol
        }
    return None