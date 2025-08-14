import asyncio
from db.db_setup import SessionLocal, User, ArbitrageHistory
import random

DEMO_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'BNB/USDT', 'ADA/USDT', 'DOGE/USDT',
    'SOL/USDT', 'DOT/USDT', 'LTC/USDT', 'LINK/USDT', 'MATIC/USDT', 'TRX/USDT',
    'UNI/USDT', 'ATOM/USDT', 'AVAX/USDT', 'FTM/USDT', 'ALGO/USDT', 'ICP/USDT',
    'AAVE/USDT', 'SAND/USDT', 'FIL/USDT', 'MANA/USDT', 'AXS/USDT', 'THETA/USDT'
]

async def run_demo_for_user(user):
    session = SessionLocal()
    for symbol in DEMO_SYMBOLS:
        buy_price = random.uniform(1, 100)
        sell_price = buy_price + random.uniform(0.1, 5)
        net_profit = sell_price - buy_price
        arb = ArbitrageHistory(
            user_id=user.id,
            symbol=symbol,
            buy_exchange='DemoBuy',
            sell_exchange='DemoSell',
            buy_price=buy_price,
            sell_price=sell_price,
            amount_base=1,
            amount_quote=buy_price,
            gross_spread_percent=(sell_price - buy_price)/buy_price*100,
            est_fees_percent=0,
            bot_fee_percent=0,
            net_profit_quote=net_profit,
            success=True,
            error=None
        )
        session.add(arb)
        session.commit()
    session.close()

async def run_demo_for_all_users():
    session = SessionLocal()
    users = session.query(User).filter_by(trading_active=True).all()
    session.close()
    for user in users:
        await run_demo_for_user(user)
