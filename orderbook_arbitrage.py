class OrderBookArb:
    def __init__(self, clients, user, settings):
        self.clients = clients
        self.user = user
        self.settings = settings

    def scan(self):
        opps = []
        symbols = ['BTC/USDT']
        for s in symbols:
            for name, c in self.clients.items():
                try:
                    orderbook = c.fetch_order_book(s)
                    asks = orderbook.get('asks', [])
                    bids = orderbook.get('bids', [])
                    opps.append({'type':'orderbook','symbol':s,'exchange':name,'est_profit':0.0})
                except Exception:
                    continue
        return opps

    def execute(self, opp):
        return {'status':'simulated','opp':opp}
