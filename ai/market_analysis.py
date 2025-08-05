import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
from typing import List, Dict
from exchange.binance import BinanceAPI

class MarketAnalyzer:
    def __init__(self):
        self.binance = BinanceAPI()
        self.anomaly_detector = IsolationForest(contamination=0.05)
    
    async def find_arbitrage_opportunities(self) -> List[Dict]:
        """
        العثور على فرص المراجحة بين الأسواق
        مع ضمان عدم وجود مخاطر كبيرة
        """
        # الحصول على بيانات الأسعار من منصات متعددة
        prices = await self._fetch_market_prices()
        
        # تحليل البيانات باستخدام الذكاء الاصطناعي
        opportunities = self._analyze_prices(prices)
        
        # تصفية الفرص الخطرة
        safe_opportunities = self._filter_risky_opportunities(opportunities)
        
        return safe_opportunities[:5]  # أفضل 5 فرص
    
    async def _fetch_market_prices(self) -> pd.DataFrame:
        """جمع بيانات الأسعار من منصات متعددة"""
        # هنا ندمج بيانات من بينانس ومنصات أخرى
        binance_prices = await self.binance.get_all_prices()
        # يمكن إضافة منصات أخرى هنا
        
        # معالجة البيانات في DataFrame
        df = pd.DataFrame(binance_prices)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def _analyze_prices(self, df: pd.DataFrame) -> List[Dict]:
        """تحليل الأسعار باستخدام خوارزميات الذكاء الاصطناعي"""
        # حساب فروق الأسعار
        df['price_diff'] = df['ask'] - df['bid']
        
        # الكشف عن الشذوذ (الفرص غير الطبيعية)
        features = df[['price', 'volume', 'price_diff']].values
        df['anomaly_score'] = self.anomaly_detector.fit_predict(features)
        
        # تصفية الفرص الجيدة
        good_opportunities = df[df['anomaly_score'] == 1]
        
        # تحويل إلى قواميس
        opportunities = []
        for _, row in good_opportunities.iterrows():
            opportunity = {
                'symbol': row['symbol'],
                'buy_at': row['bid'],
                'sell_at': row['ask'],
                'profit_percentage': (row['price_diff'] / row['bid']) * 100,
                'volume': row['volume'],
                'exchange': 'binance',
                'timestamp': row['timestamp'],
                'risk_score': 0  # سيتم حسابه لاحقًا
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _filter_risky_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """تصفية الفرص الخطرة باستخدام تحليل المخاطر"""
        safe_opportunities = []
        
        for opp in opportunities:
            # حساب درجة المخاطرة
            risk_score = self._calculate_risk_score(opp)
            opp['risk_score'] = risk_score
            
            # قبول فقط الفرص ذات المخاطرة المنخفضة
            if risk_score < 0.3:  # مثال: 0.3 يعني 30% مخاطرة
                safe_opportunities.append(opp)
        
        # ترتيب الفرص حسب نسبة الربح
        return sorted(safe_opportunities, key=lambda x: x['profit_percentage'], reverse=True)
    
    def _calculate_risk_score(self, opportunity: Dict) -> float:
        """حساب درجة المخاطرة باستخدام عدة عوامل"""
        # عوامل المخاطرة
        volatility_risk = min(1, opportunity['volume'] / 1000000)  # مثال بسيط
        time_risk = 0.1  # افتراضياً
        exchange_risk = 0.05  # بينانس آمنة نسبياً
        
        # مجموع مرجح لعوامل المخاطرة
        total_risk = (volatility_risk * 0.6 + time_risk * 0.2 + exchange_risk * 0.2)
        
        return total_risk
    
    async def monitor_active_trades(self):
        """مراقبة الصفقات النشطة وإيقافها إذا لزم الأمر"""
        active_trades = await self._get_active_trades()
        
        for trade in active_trades:
            current_status = await self._check_trade_status(trade)
            
            if current_status['potential_loss'] > 0:
                await self._stop_trade(trade, reason="خسارة محتملة")
    
    async def _get_active_trades(self):
        """الحصول على الصفقات النشطة من قاعدة البيانات"""
        # سيتم تنفيذ هذا عبر ORM
        pass
    
    async def _check_trade_status(self, trade):
        """فحص حالة الصفقة الحالية"""
        # الحصول على أحدث بيانات السعر
        current_price = await self.binance.get_price(trade['symbol'])
        
        # حساب الربح/الخسارة المحتملة
        potential_profit = (current_price - trade['entry_price']) * trade['amount']
        potential_loss = -potential_profit if potential_profit < 0 else 0
        
        return {
            'potential_profit': potential_profit,
            'potential_loss': potential_loss,
            'current_price': current_price
        }
    
    async def _stop_trade(self, trade, reason):
        """إيقاف الصفقة لحماية رأس المال"""
        # تنفيذ أمر بيع إذا لزم الأمر
        if trade['position'] == 'long':
            await self.binance.create_order(
                symbol=trade['symbol'],
                side='sell',
                amount=trade['amount']
            )
        
        # تحديث حالة الصفقة في قاعدة البيانات
        # await update_trade_status(trade['id'], 'stopped', reason)
