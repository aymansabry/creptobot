def hedge_strategy(balance, risk_level=0.2):
    """
    توزيع ذكي للاستثمار مع تحوط ضد الخسائر
    """
    safe_amount = balance * (1 - risk_level)
    risky_amount = balance * risk_level
    return {
        "safe": round(safe_amount, 2),
        "risky": round(risky_amount, 2)
    }

def calculate_profit(buy_price, sell_price, amount):
    return round((sell_price - buy_price) * amount, 2)
