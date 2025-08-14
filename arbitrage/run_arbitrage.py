import asyncio
import ccxt
from db.db_setup import SessionLocal, ArbitrageHistory, ExchangeCredential, User
from utils.helpers import execute_order_on_exchange
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

async def analyze_with_openai(symbol, buy_price, sell_price):
    prompt = f"تحليل سريع لزوج {symbol}:\nسعر الشراء: {buy_price}\nسعر البيع: {sell_price}\nاعطِ توقع إذا سيزيد السعر أم سينخفض."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60
        )
        return response.choices[0].message['content'].strip()
    except:
        return "لا يمكن الحصول على تحليل حالياً."

async def run_arbitrage_for_user(user):
    session = SessionLocal()
    exchanges = session.query(ExchangeCredential).filter_by(user_id=user.id, active=True).all()
    if len(exchanges) < 2:
        session.close()
        return
    symbols_set = set()
    for ex in exchanges:
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
            except:
                continue
    symbols = list(symbols_set)
    for symbol in symbols:
        prices = {}
        for ex in exchanges:
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