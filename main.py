import asyncio
from core.trading_engine import TradingEngine
from wallet.manager import WalletManager
from monitoring.performance import PerformanceMonitor

async def main():
    trader = TradingEngine()
    wallet = WalletManager()
    monitor = PerformanceMonitor()
    
    while True:
        await trader.execute_auto_trade()
        await wallet.rebalance_portfolio()
        report = monitor.generate_daily_report()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
