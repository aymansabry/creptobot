from exchanges.binance import BinanceAPI
from ai.arbitrage import ArbitrageFinder
from db.crud import record_trade
from utils.logger import trade_logger

class TradingEngine:
    def __init__(self):
        self.binance = BinanceAPI()
        self.arbitrage_finder = ArbitrageFinder()
    
    async def execute_auto_trade(self):
        opportunities = self.arbitrage_finder.find_opportunities()
        best_trade = self.arbitrage_finder.select_best_trade(opportunities)
        
        if best_trade:
            execution_result = await self.binance.execute_arbitrage(best_trade)
            record_trade(execution_result)
            return execution_result
        return None
