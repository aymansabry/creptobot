class TriangularArb:
    def __init__(self, clients, user, settings):
        self.clients = clients
        self.user = user
        self.settings = settings

    def scan(self):
        opps = []
        for name, c in self.clients.items():
            try:
                # simplified triangle set
                symbols = [('BTC/USDT','ETH/USDT','BTC/ETH')]
                for s in symbols:
                    try:
                        t0 = c.fetch_ticker(s[0])
                        t1 = c.fetch_ticker(s[1])
                        t2 = c.fetch_ticker(s[2])
                        est_profit = 0.0
                        if est_profit > self.settings['MIN_PROFIT_USDT']:
                            opps.append({'type':'triangular','exchange':name,'symbols':s,'est_profit':est_profit})
                    except Exception:
                        continue
            except Exception:
                continue
        return opps

    def execute(self, opp):
        return {'status':'simulated','opp':opp}
