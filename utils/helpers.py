# utils/helpers.py
def format_currency(amount):
    return f"{amount:,.2f} $"

def get_plan_distribution(plan):
    if plan == "safe":
        return {"fixed": 0.7, "flex": 0.3, "risk": 0.0}
    elif plan == "balanced":
        return {"fixed": 0.4, "flex": 0.4, "risk": 0.2}
    elif plan == "aggressive":
        return {"fixed": 0.2, "flex": 0.3, "risk": 0.5}
    return {"fixed": 1.0, "flex": 0.0, "risk": 0.0}