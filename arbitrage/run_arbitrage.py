import asyncio
import logging
from db.database import SessionLocal
from db.models import User, ExchangeCredential, ArbitrageHistory
from utils.helpers import execute_order_on_exchange, analyze_with_openai

logger = logging.getLogger(__name__)

async def fetch_user_exchanges(session, user_id):
    return session.query(ExchangeCredential).filter_by(user_id=user_id, active=True).all()

async def fetch_symbols_for_arbitrage(user_exchanges):
    import ccxt
    symbols_set = set()
    for ex in user_exchanges:
        exchange_class = getattr(ccxt, ex.exchange_id.lower(), None)
        if exchange_class:
            exchange = exchange_class({
                'apiKey': ex.api_key,
                'secret': ex.secret,
                'password': ex.passphrase or ''
            })
            try:
                tickers = exchange.fetch_tickers()
                symbols_set.update(tickers.keys())
            except Exception as e:
                logger.error(f"Error fetching symbols for {ex.exchange_id}: {e}")
    return list(symbols_set)

async def run_arbitrage_for_user(user):
    session = SessionLocal()
    exchanges = await fetch_user_exchanges(session, user.id)
    if len(exchanges) < 2:
        session.close()
        return

    symbols = await fetch_symbols_for_arbitrage(exchanges)
    for symbol in symbols:
        prices = {}
        for ex in exchanges:
            import ccxt
            exchange_class = getattr(ccxt, ex.exchange_id.lower(), None)
            if exchange_class:
                exchange = exchange_class({
                    'apiKey': ex.api_key,
                    'secret': ex.secret,
                    'password': ex.passphrase or ''
                })
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    prices[ex.exchange_id] = ticker['last']
                except:
                    continue

        if len(prices) < 2:
            continue

        buy_ex, sell_ex = min(prices, key=prices.get), max(prices, key=prices.get)
        buy_price, sell_price = prices[buy_ex], prices[sell_ex]
        gross_spread = (sell_price - buy_price) / buy_price * 100
        est_fees_percent = 0.1
        bot_fee_percent = 0.05
        net_profit = gross_spread - est_fees_percent - bot_fee_percent

        analysis = await analyze_with_openai(symbol, buy_price, sell_price)

        success_buy = await execute_order_on_exchange(buy_ex, 'buy', symbol, 1, buy_price, exchanges[0])
        success_sell = await execute_order_on_exchange(sell_ex, 'sell', symbol, 1, sell_price, exchanges[1])
        success = success_buy and success_sell

        # حفظ النتائج في قاعدة البيانات
        arb = ArbitrageHistory(
            user_id=user.id,
            symbol=symbol,
            buy_exchange=buy_ex,
            sell_exchange=sell_ex,
            buy_price=buy_price,
            sell_price=sell_price,
            amount_base=1,
            amount_quote=buy_price,
            gross_spread_percent=gross_spread,
            est_fees_percent=est_fees_percent,
            bot_fee_percent=bot_fee_percent,
            net_profit_quote=net_profit,
            success=success,
            error=None if success else "فشل التنفيذ"
        )
        session.add(arb)
        session.commit()

    session.close()

async def run_arbitrage_for_all_users():
    session = SessionLocal()
    users = session.query(User).filter_by(trading_active=True).all()
    session.close()
    for user in users:
        await run_arbitrage_for_user(user)

async def run_arbitrage_demo():
    # استعراض وهمي للمراجحة بدون تنفيذ فعلي
    session = SessionLocal()
    users = session.query(User).filter_by(trading_active=True).all()
    session.close()
    return "تم تشغيل الاستثمار الوهمي لكل المستخدمين النشطين."