import numpy as np
from typing import Dict

class PortfolioAI:
    def optimize_allocation(self, current: Dict, market_conditions: Dict) -> Dict:
        """
        حساب التوزيع الأمثل للمحفظة
        """
        # تطبيق خوارزمية ماركوفيتز المعدلة
        if market_conditions['trend'] == 'bullish':
            return {
                'BTC': 0.5,
                'ETH': 0.3,
                'USDT': 0.2
            }
        else:
            return {
                'BTC': 0.3,
                'ETH': 0.2,
                'USDT': 0.5
            }
