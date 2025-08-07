import asyncio
from utils.logger import setup_logging
from core.trading_engine import TradingEngine

async def main():
    setup_logging()
    engine = TradingEngine()
    
    # مثال لتنفيذ صفقة
    result = await engine.execute_trade('BTCUSDT', 0.001)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
