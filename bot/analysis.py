import logging
from typing import List, Dict, Any
from ccxt import Exchange
from config import Config
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, exchange: Exchange):
        self.exchange = exchange
    
    def get_top_opportunities(self) -> List[Dict[str, Any]]:
        """Get top 5 arbitrage opportunities"""
        try:
            # Fetch all tickers
            tickers = self.exchange.fetch_tickers()
            
            # Filter USDT pairs and convert to DataFrame
            usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
            df = pd.DataFrame.from_dict(usdt_pairs, orient='index')
            
            # Calculate spreads
            df['spread_pct'] = (df['ask'] - df['bid']) / df['bid'] * 100
            df = df[df['spread_pct'] >= Config.MIN_PROFIT_PERCENT + Config.BOT_FEE_PERCENT]
            df = df.sort_values('spread_pct', ascending=False)
            
            # Format results
            return [{
                'symbol': idx,
                'buy_price': row['bid'],
                'sell_price': row['ask'],
                'profit_percent': row['spread_pct'] - Config.BOT_FEE_PERCENT,
                'description_ar': f"شراء {idx.split('/')[0]} بسعر {row['bid']:.6f} بيع {row['ask']:.6f} (ربح {row['spread_pct']-Config.BOT_FEE_PERCENT:.2f}%)",
                'description_en': f"Buy {idx} at {row['bid']:.6f} Sell at {row['ask']:.6f} (Profit {row['spread_pct']-Config.BOT_FEE_PERCENT:.2f}%)"
            } for idx, row in df.head(5).iterrows()]
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return []
