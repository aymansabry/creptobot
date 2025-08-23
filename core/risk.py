from config import settings

class Risk:
    def __init__(self, markets):
        self.markets = markets

    def min_notional_ok(self, symbol, notional_usdt, price):
        m = self.markets.get(symbol)
        if not m:
            return False, "symbol_not_found"
        limits = m.get('limits', {})
        min_cost = limits.get('cost', {}).get('min', None)
        min_amount = limits.get('amount', {}).get('min', None)
        if min_cost and (notional_usdt < min_cost):
            return False, f"min_notional_violation: requires >= {min_cost} {m.get('quote') or 'quote'}"
        if price and min_amount:
            amt = notional_usdt / price
            if amt < min_amount:
                return False, f"min_amount_violation: amount {amt:.8f} < min {min_amount}"
        return True, None

    def can_execute(self, route_legs, get_price_fn, notional_usdt):
        for (symbol, side, frm, to) in route_legs:
            px = get_price_fn(symbol, side)
            ok, reason = self.min_notional_ok(symbol, notional_usdt, px)
            if not ok:
                return False, reason
        return True, None
