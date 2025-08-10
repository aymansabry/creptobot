from decimal import Decimal
class SimpleArb:
    def __init__(self, clients, user, settings):
        self.clients = clients
        self.user = user
        self.settings = settings

    def scan(self):
        symbols = ['BTC/USDT','ETH/USDT']
        results = []
        for s in symbols:
            data = {}
            for name, c in self.clients.items():
                try:
                    t = c.fetch_ticker(s)
                    data[name] = {'ask': t.get('ask'), 'bid': t.get('bid')}
                except Exception:
                    continue
            if len(data) < 2:
                continue
            best_buy = min(((n,d['ask']) for n,d in data.items() if d['ask']), key=lambda x: x[1])
            best_sell = max(((n,d['bid']) for n,d in data.items() if d['bid']), key=lambda x: x[1])
            if best_buy[0] == best_sell[0]:
                continue
            est_profit = self.estimate_profit(best_buy, best_sell, s)
            if est_profit > self.settings['MIN_PROFIT_USDT']:
                results.append({'type':'simple','symbol':s,'buy_ex':best_buy[0],'buy_price':best_buy[1],'sell_ex':best_sell[0],'sell_price':best_sell[1],'est_profit':est_profit})
        return results

    def estimate_profit(self, buy_tuple, sell_tuple, symbol):
        buy_ex, buy_price = buy_tuple
        sell_ex, sell_price = sell_tuple
        fee_buy = self.settings['FEE_ESTIMATE'].get(buy_ex, 0.001)
        fee_sell = self.settings['FEE_ESTIMATE'].get(sell_ex, 0.001)
        slippage = self.settings.get('SLIPPAGE_BUFFER', 0.0005)
        qty = 0.001
        cost = buy_price * qty * (1 + fee_buy + slippage)
        revenue = sell_price * qty * (1 - fee_sell - slippage)
        return float(revenue - cost)

    def check_risk(self, opp):
        return True

    def execute(self, opp):
        # simplified: log intent and return
        return {'status':'simulated','opp':opp}
