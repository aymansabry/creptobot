import asyncio
import ccxt
from db.db_setup import SessionLocal, User, ExchangeCredential, ArbitrageHistory
from utils.helpers import execute_order_on_exchange
from db.encryption import decrypt_value
import logging

logger = logging.getLogger(__name__)

TARGET_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'BNB/USDT', 'ADA/USDT', 'DOGE/USDT',
    'SOL/USDT', 'DOT/USDT', 'LTC/USDT', 'LINK/USDT', 'MATIC/USDT', 'TRX/USDT',
    'UNI/USDT', 'ATOM/USDT', 'AVAX/USDT', 'FTM/USDT', 'ALGO/USDT', 'ICP/USDT',
    'AAVE/USDT', 'SAND/USDT', 'FIL/USDT', 'MANA/USDT', 'AXS/USDT', 'THETA/USDT'
]

async def run_arbitrage_for_user(user):
    session = SessionLocal()
    exchanges = session.query(ExchangeCredential).filter_by(user_id=user.id, active=True).all()
    if len(exchanges) < 2:
        session.close()
        return

    symbols_set = set()
    for ex in exchanges:
        try:
            exchange_class = getattr(ccxt, ex.exchange_id.lower(), None)
            if exchange_class:
                exchange = exchange_class({
                    'apiKey': decrypt_value(ex.api_key),
                    'secret': decrypt_value(ex.secret),
                    'password': decrypt_value(ex.passphrase or '')
                })
                tickers = exchange.fetch_tickers()
                symbols_set.update([s for s in tickers.keys() if s in TARGET_SYMBOLS])
        except Exception as e:
            logger.error(f"Error fetching tickers for {ex.exchange_id}: {e}")

    symbols = list(symbols_set)
    for symbol in symbols:
        prices = {}
        for ex in exchanges:
            try:
                exchange_class = getattr(ccxt, ex.exchange_id.lower(), None)
                if exchange_class:
                    exchange = exchange_class({
                        'apiKey': decrypt_value(ex.api_key),
                        'secret': decrypt_value(ex.secret),
                        'password': decrypt_value(ex.passphrase or '')
                    })
                    ticker = exchange.fetch_ticker(symbol)
                    prices[ex.exchange_id] = ticker['last']
            except Exception as e:
                logger.warning(f"{ex.exchange_id} skipped {symbol}: {e}")
                continue

        if len(prices) < 2:
            continue

        buy_ex, sell_ex = min(prices, key=prices.get), max(prices, key=prices.get)
        buy_price, sell_price = prices[buy_ex], prices[sell_ex]
        gross_spread = (sell_price - buy_price) / buy_price * 100
        est_fees_percent = 0.1
        bot_fee_percent = 0.05
        net_profit = gross_spread - est_fees_percent - bot_fee_percent

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
