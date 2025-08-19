from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def find_arbitrage_opportunities(pairs):
    prices = {}
    for pair in pairs:
        try:
            ticker = client.get_symbol_ticker(symbol=pair)
            prices[pair] = float(ticker['price'])
        except:
            continue

    opportunities = []
    for base in ['USDT', 'BTC', 'ETH']:
        for a in pairs:
            for b in pairs:
                if a != b and a.endswith(base) and b.startswith(base):
                    try:
                        price_a = prices[a]
                        price_b = prices[b]
                        profit = (1 / price_a) * price_b - 1
                        if profit > 0.005:  # ربح أكثر من 0.5%
                            opportunities.append({
                                'path': [a, b],
                                'profit': round(profit * 100, 2)
                            })
                    except:
                        continue
    return opportunities
