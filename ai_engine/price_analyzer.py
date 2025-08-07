import ccxt
import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime

class PriceAnalyzer:
    def __init__(self, exchanges: List[str]):
        self.exchanges = {name: getattr(ccxt, name)() for name in exchanges}
        
    async def fetch_prices(self, symbols: List[str]) -> Dict:
        prices = {}
        for exchange_name, exchange in self.exchanges.items():
            try:
                prices[exchange_name] = {}
                for symbol in symbols:
                    ticker = exchange.fetch_ticker(symbol)
                    prices[exchange_name][symbol] = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'last': ticker['last'],
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"Error fetching prices from {exchange_name}: {str(e)}")
        return prices
    
    def find_arbitrage_opportunities(self, prices: Dict, min_profit: float = 0.015) -> List[Dict]:
        opportunities = []
        symbols = list(next(iter(prices.values())).keys()
        
        for symbol in symbols:
            buy_exchange = None
            sell_exchange = None
            max_bid = 0
            min_ask = float('inf')
            
            for exchange_name, exchange_prices in prices.items():
                if symbol in exchange_prices:
                    bid = exchange_prices[symbol]['bid']
                    ask = exchange_prices[symbol]['ask']
                    
                    if bid > max_bid:
                        max_bid = bid
                        buy_exchange = exchange_name
                    
                    if ask < min_ask:
                        min_ask = ask
                        sell_exchange = exchange_name
            
            if buy_exchange and sell_exchange and buy_exchange != sell_exchange:
                spread = max_bid - min_ask
                profit_percentage = spread / min_ask
                
                if profit_percentage >= min_profit:
                    opportunities.append({
                        'symbol': symbol,
                        'buy_from': sell_exchange,
                        'sell_to': buy_exchange,
                        'buy_price': min_ask,
                        'sell_price': max_bid,
                        'profit_percentage': profit_percentage * 100,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return sorted(opportunities, key=lambda x: x['profit_percentage'], reverse=True)[:5]
