# services/risk_manager.py
def should_hedge(market_drop_percent):
    return market_drop_percent >= 10  # لو السوق نزل 10% أو أكثر

def adjust_distribution(current_plan):
    if current_plan == "aggressive":
        return {"fixed": 0.5, "flex": 0.3, "risk": 0.2}
    return None