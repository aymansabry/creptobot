from decimal import Decimal

def calc_profit(sell_price: Decimal, buy_price: Decimal, amount: Decimal, fees_pct: Decimal = Decimal('0.001')) -> Decimal:
    """
    Calculates the gross profit of a trade.
    Assumes fees are taken from the base currency on buy and quote currency on sell.
    """
    buy_cost = buy_price * amount * (Decimal('1') + fees_pct)
    sell_income = sell_price * amount * (Decimal('1') - fees_pct)
    return sell_income - buy_cost
