import random
from decimal import Decimal

# نموذج لصفقة أربيتراج وهمية
def find_profitable_opportunity(min_profit_percent: float) -> dict | None:
    platforms = ["Binance", "KuCoin", "Bybit", "OKX"]
    buy = random.choice(platforms)
    sell = random.choice([p for p in platforms if p != buy])

    profit_percent = round(random.uniform(2, 5), 2)

    if profit_percent < min_profit_percent:
        return None

    return {
        "buy_from": buy,
        "sell_to": sell,
        "profit_percent": profit_percent
    }

def execute_trade(amount: Decimal, profit_percent: float):
    net_profit = amount * Decimal(profit_percent / 100)
    return round(net_profit, 6)
