import asyncio
from utils.logger import setup_logging
from core.trading_engine import TradingEngine

async def main():
    setup_logging()
    engine = TradingEngine()
    
    # مثال لتنفيذ صفقة مع التحقق من الرصيد
    trading_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    trade_amount = 10  # USDT
    
    for pair in trading_pairs:
        result = await engine.execute_trade(pair, trade_amount)
        
        if result['status'] == 'completed':
            print(f"Trade successful! Profit: {result['profit']:.2f} USDT")
        else:
            print(f"Trade failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
