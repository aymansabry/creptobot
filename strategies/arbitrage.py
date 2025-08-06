from apis.binance import BinanceAPI
import numpy as np

class RealArbitrage:
    def __init__(self, binance_api: BinanceAPI):
        self.api = binance_api
    
    async def scan_opportunities(self):
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        prices = {}
        
        async for data in self.api.get_real_time_data(symbols):
            prices[data['s']] = float(data['p'])
            if len(prices) == len(symbols):
                btc_eth = prices['BTCUSDT'] / prices['ETHUSDT']
                # تحليل الفروقات هنا
                if btc_eth > 1.02:  # فرق 2%
                    yield {
                        'symbol': 'BTC/ETH',
                        'profit': round((btc_eth - 1) * 100, 2),
                        'action': 'buy_eth_sell_btc'
                    }
