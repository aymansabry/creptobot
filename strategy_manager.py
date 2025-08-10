from simple_arbitrage import SimpleArb
from triangular_arbitrage import TriangularArb
from orderbook_arbitrage import OrderBookArb

class StrategyManager:
    def __init__(self, clients, user, settings):
        self.clients = clients
        self.user = user
        self.settings = settings
        self.simple = SimpleArb(clients, user, settings)
        self.triangular = TriangularArb(clients, user, settings)
        self.orderbook = OrderBookArb(clients, user, settings)

    def evaluate(self):
        opps = []
        opps.extend(self.simple.scan())
        opps.extend(self.triangular.scan())
        opps.extend(self.orderbook.scan())
        opps = sorted(opps, key=lambda x: x.get('est_profit',0), reverse=True)
        return opps

    def execute_best(self):
        opps = self.evaluate()
        for o in opps:
            # very basic risk check placeholder
            if o.get('est_profit',0) > self.settings.get('MIN_PROFIT_USDT', 1.0):
                if o['type'] == 'simple':
                    return self.simple.execute(o)
                if o['type'] == 'triangular':
                    return self.triangular.execute(o)
                if o['type'] == 'orderbook':
                    return self.orderbook.execute(o)
        return None
