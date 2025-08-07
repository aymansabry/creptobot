import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, List

class RiskAssessor:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05)
        
    def assess_risk(self, opportunity: Dict, historical_data: List[Dict]) -> float:
        # تحليل السيولة
        liquidity_risk = self._calculate_liquidity_risk(opportunity)
        
        # تحليل التقلبات
        volatility_risk = self._calculate_volatility_risk(opportunity, historical_data)
        
        # تحليل الشذوذ
        anomaly_risk = self._detect_anomalies(opportunity, historical_data)
        
        # مجموع المخاطر المرجح
        total_risk = 0.4 * liquidity_risk + 0.4 * volatility_risk + 0.2 * anomaly_risk
        
        return round(total_risk, 2)
    
    def _calculate_liquidity_risk(self, opportunity: Dict) -> float:
        # تحليل حجم الطلب والعرض
        bid_ask_spread = (opportunity['sell_price'] - opportunity['buy_price']) / opportunity['buy_price']
        return min(bid_ask_spread * 10, 1.0)
    
    def _calculate_volatility_risk(self, opportunity: Dict, historical_data: List[Dict]) -> float:
        # حساب الانحراف المعياري للأسعار التاريخية
        prices = [d['last'] for d in historical_data if d['symbol'] == opportunity['symbol']]
        if len(prices) < 2:
            return 0.5
        
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        return min(volatility * 5, 1.0)
    
    def _detect_anomalies(self, opportunity: Dict, historical_data: List[Dict]) -> float:
        # استخدام Isolation Forest للكشف عن الشذوذ
        features = []
        for d in historical_data[-100:]:
            if d['symbol'] == opportunity['symbol']:
                features.append([d['last'], d['volume']])
        
        if len(features) < 10:
            return 0.3
            
        self.model.fit(features)
        anomaly_score = self.model.decision_function([[opportunity['last'], opportunity.get('volume', 0)]])
        return max(0, 1 - (anomaly_score + 0.5))  # تحويل النتيجة إلى مقياس 0-1
