from typing import Dict, Optional
from services.exchange_api import BinanceAPI, KuCoinAPI
from config import Config
import asyncio

class ArbitrageEngine:
    def __init__(self):
        self.binance = BinanceAPI()
        self.kucoin = KuCoinAPI()
        self.min_profit_percentage = 0.005  # 0.5%
    
    async def find_opportunity(self, symbol: str, credentials: Dict[str, Dict[str, str]]) -> Optional[Dict[str, float]]:
        binance_price = self.binance.get_ticker_price(symbol, credentials['binance'])
        kucoin_price = self.kucoin.get_ticker_price(symbol, credentials['kucoin'])
        
        if not binance_price or not kucoin_price:
            return None
        
        if kucoin_price < binance_price * (1 - self.min_profit_percentage):
            return {
                'symbol': symbol,
                'buy_exchange': 'kucoin',
                'sell_exchange': 'binance',
                'buy_price': kucoin_price,
                'sell_price': binance_price,
                'potential_profit': binance_price - kucoin_price,
                'profit_percentage': (binance_price - kucoin_price) / kucoin_price
            }
        elif binance_price < kucoin_price * (1 - self.min_profit_percentage):
            return {
                'symbol': symbol,
                'buy_exchange': 'binance',
                'sell_exchange': 'kucoin',
                'buy_price': binance_price,
                'sell_price': kucoin_price,
                'potential_profit': kucoin_price - binance_price,
                'profit_percentage': (kucoin_price - binance_price) / binance_price
            }
        return None
    
    async def execute_trade(self, opportunity: Dict[str, float], amount: float, credentials: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        # هنا يتم تنفيذ الصفقة الفعلية
        # هذا مثال مبسط بدون تنفيذ حقيقي لأسباب أمنية
        return {
            'status': 'success',
            'executed_amount': amount,
            'realized_profit': opportunity['potential_profit'] * amount,
            'fees': 0.001 * amount * 2,  # رسوم الشراء والبيع
            'timestamp': datetime.now().isoformat()
        }
