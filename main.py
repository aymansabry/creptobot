import os
import asyncio
import ccxt.async_support as ccxt
from dotenv import load_dotenv

load_dotenv()

EXCHANGES = os.getenv("EXCHANGES", "binance,kucoin,bitget").split(",")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", 10))  # مبلغ التداول من المستخدم
MIN_PROFIT_PCT = float(os.getenv("MIN_PROFIT_PCT", 0.2))
LIVE_TRADE = os.getenv("LIVE_TRADE", "false").lower() == "true"

async def fetch_opportunities(exchange):
    try:
        markets = await exchange.load_markets()
        cycles = []
        symbols = [s for s in markets if s.endswith('/USDT')]
        for base1 in symbols:
            for base2 in symbols:
                if base1 != base2:
                    mid_symbol = f"{markets[base1]['base']}/{markets[base2]['base']}"
                    if mid_symbol in markets:
                        cycles.append((base1, mid_symbol, base2))
        tasks = [check_cycle(exchange, c) for c in cycles]
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Error fetching opportunities on {exchange.id}: {e}")

async def check_cycle(exchange, cycle):
    try:
        start, mid, end = cycle
        o1 = await exchange.fetch_ticker(start)
        o2 = await exchange.fetch_ticker(mid)
        o3 = await exchange.fetch_ticker(end)

        # الأسعار
        rate1 = o1['ask']
        rate2 = o2['ask']
        rate3 = o3['bid']

        # حساب الربح
        amount_a = TRADE_AMOUNT / rate1
        amount_b = amount_a / rate2
        final_amount = amount_b * rate3
        profit_pct = ((final_amount - TRADE_AMOUNT) / TRADE_AMOUNT) * 100

        if profit_pct >= MIN_PROFIT_PCT:
            print(f"[{exchange.id}] فرصة: {cycle} | ربح {profit_pct:.2f}%")
            if LIVE_TRADE:
                await execute_trade(exchange, cycle)
    except Exception as e:
        pass

async def execute_trade(exchange, cycle):
    print(f"تنفيذ الصفقة {cycle} على {exchange.id} بمبلغ {TRADE_AMOUNT} USDT")
    # تنفيذ فعلي Placeholder

async def main():
    exchange_instances = []
    for ex in EXCHANGES:
        ex = ex.strip().lower()
        if hasattr(ccxt, ex):
            exchange_instances.append(getattr(ccxt, ex)({
                'apiKey': os.getenv(f"{ex.upper()}_API_KEY"),
                'secret': os.getenv(f"{ex.upper()}_API_SECRET"),
                'password': os.getenv(f"{ex.upper()}_PASSWORD", None),
            }))

    await asyncio.gather(*(fetch_opportunities(ex) for ex in exchange_instances))

    for ex in exchange_instances:
        await ex.close()

if __name__ == "__main__":
    asyncio.run(main())
