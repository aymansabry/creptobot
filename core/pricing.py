from config import settings
FEES = {"taker": 0.001}

def simulate_route(route_legs, get_price_fn):
    notional = settings.leg_notional_usdt
    value = notional
    fees_total_pct = 0.0
    for (symbol, side, frm, to) in route_legs:
        px = get_price_fn(symbol, side)
        if not px:
            return None
        px = px * (1 + settings.max_slippage_pct/100.0) if side=='buy' else px * (1 - settings.max_slippage_pct/100.0)
        fee_pct = FEES['taker']*100
        fees_total_pct += fee_pct
        if side == 'buy':
            qty = value / px
            value = qty
        else:
            proceeds = value * px
            value = proceeds
    gross_pct = (value - notional) / notional * 100
    net_pct = gross_pct - fees_total_pct
    return gross_pct, net_pct
