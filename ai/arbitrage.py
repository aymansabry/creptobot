import numpy as np
from exchanges.binance import BinanceAPI
from exchanges.kucoin import KuCoinAPI
from exchanges.bybit import BybitAPI

class ArbitrageFinder:
    def __init__(self):
        self.binance = BinanceAPI()
        self.kucoin = KuCoinAPI()
        self.bybit = BybitAPI()
    
    def find_opportunities(self) -> list:
        # الحصول على بيانات الأسعار من جميع المنصات
        binance_prices = self._get_binance_prices()
        kucoin_prices = self._get_kucoin_prices()
        bybit_prices = self._get_bybit_prices()
        
        # تحليل فرص المراجحة
        opportunities = []
        for symbol in binance_prices:
            price_diff = self._calculate_price_difference(
                binance_prices[symbol],
                kucoin_prices.get(symbol, {}),
                bybit_prices.get(symbol, {})
            )
            if price_diff['profit'] > 0.5:  # فرق ربح أكثر من 0.5%
                opportunities.append(price_diff)
        
        return opportunities
    
    def select_best_trade(self, opportunities: list) -> dict:
        if not opportunities:
            return None
        
        # تطبيق خوارزمية الاختيار
        return max(opportunities, key=lambda x: x['profit']/x['risk'])
