from exchange.binance_client import BinanceClient
from config import settings

class Executor:
    def __init__(self, markets, api_key=None, api_secret=None):
        self.client = BinanceClient(api_key, api_secret)
        self.markets = markets

    def _amount_for_leg(self, symbol, side, price, notional_usdt):
        amt = notional_usdt / price
        step = int(self.markets[symbol]['precision'].get('amount', 8))
        min_step = 10**(-step)
        return round(max(amt, min_step), step)

    def market_price(self, symbol, side):
        book = self.client.fetch_order_book(symbol, 5)
        if not book:
            return None
        return book['asks'][0][0] if side=='buy' else book['bids'][0][0]

    def ensure_bnb_reserve(self, min_bnb, topup_usdt):
        bal = self.client.fetch_balance()
        bnb_free = bal.get('free', {}).get('BNB', 0.0)
        if bnb_free >= min_bnb:
            return None
        price = self.market_price('BNB/USDT', 'buy')
        if not price:
            return None
        amt = round(topup_usdt / price, 6)
        return self.client.create_market_order('BNB/USDT', 'buy', amt)

    def execute_route(self, route_legs, notional_usdt):
        self.ensure_bnb_reserve(settings.bnb_min_reserve, settings.bnb_topup_usdt)
        fills = []
        for (symbol, side, frm, to) in route_legs:
            px = self.market_price(symbol, side)
            if not px:
                return {"ok": False, "reason": "no_price", "where": symbol}
            amt = self._amount_for_leg(symbol, side, px, notional_usdt)
            order = self.client.create_market_order(symbol, side, amt)
            fills.append({"symbol": symbol, "side": side, "amt": amt, "price": px, "order": order})
        return {"ok": True, "fills": fills}

    def settle_fee(self, user_id, profit_usdt, fee_pct, withdraw_addr=None):
        fee = profit_usdt * fee_pct / 100.0
        if fee <= 0:
            return {"ok": False, "reason": "zero_fee"}
        if not withdraw_addr:
            return {"ok": False, "reason": "no_withdraw_address", "fee": fee}
        try:
            tx = self.client.withdraw('USDT', fee, withdraw_addr)
            return {"ok": True, "tx": tx}
        except Exception as e:
            return {"ok": False, "reason": str(e)}
