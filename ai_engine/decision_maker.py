from typing import Dict, List
from .price_analyzer import PriceAnalyzer
from .risk_assessment import RiskAssessor

class DecisionMaker:
    def __init__(self, exchanges: List[str]):
        self.price_analyzer = PriceAnalyzer(exchanges)
        self.risk_assessor = RiskAssessor()
        
    async def get_top_opportunities(self, symbols: List[str], min_profit: float = 0.015, max_risk: float = 0.3) -> List[Dict]:
        # الحصول على الأسعار الحالية
        prices = await self.price_analyzer.fetch_prices(symbols)
        
        # اكتشاف فرص المراجحة
        opportunities = self.price_analyzer.find_arbitrage_opportunities(prices, min_profit)
        
        # تقييم المخاطر لكل فرصة
        evaluated_opportunities = []
        for opp in opportunities:
            historical_data = self._get_historical_data(opp['symbol'])
            risk = self.risk_assessor.assess_risk(opp, historical_data)
            
            if risk <= max_risk:
                opp['risk_score'] = risk
                opp['success_probability'] = 1 - risk
                evaluated_opportunities.append(opp)
        
        return sorted(evaluated_opportunities, key=lambda x: x['profit_percentage'] * x['success_probability'], reverse=True)
    
    def _get_historical_data(self, symbol: str, lookback: int = 100) -> List[Dict]:
        # في التنفيذ الفعلي، سيتم جلب البيانات من قاعدة البيانات
        # هذا نموذج بسيط لأغراض التوضيح
        return []
