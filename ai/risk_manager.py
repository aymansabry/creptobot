from datetime import datetime
from db.crud import get_daily_trades

class RiskManager:
    @staticmethod
    def calculate_trade_risk(trade_data: dict) -> float:
        # حساب مستوى المخاطرة (0-1)
        volatility = trade_data.get('volatility', 0)
        liquidity = trade_data.get('liquidity', 1)
        return min(volatility * (1/liquidity), 1)
    
    @staticmethod
    def check_daily_limit(user_id: str) -> bool:
        # التحقق من الحد اليومي
        daily_trades = get_daily_trades(user_id)
        total = sum(t['amount'] for t in daily_trades)
        return total < 10000  # حد أقصى 10,000 يومياً
