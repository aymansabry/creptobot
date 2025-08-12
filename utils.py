# utils.py
import os
import asyncio
import ccxt
import random
from dotenv import load_dotenv
import database

load_dotenv()

ALLOW_REAL_TRADES = os.getenv("ALLOW_REAL_TRADES", "false").lower() in ("1","true","yes")
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "false").lower() in ("1","true","yes")
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

async def to_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

async def validate_platform_keys(platform_name, api_key, api_secret, password=None, use_sandbox=False):
    """تحقق من صحة مفاتيح API عبر استدعاء fetch_balance (في thread)"""
    try:
        platform = platform_name.lower()
        if platform == "binance":
            ex = ccxt.binance({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
            if use_sandbox:
                # Binance testnet
                ex.urls['api'] = ex.urls.get('test') or {
                    'public': 'https://testnet.binance.vision/api/v3',
                    'private': 'https://testnet.binance.vision/api/v3'
                }
        elif platform == "kucoin":
            ex = ccxt.kucoin({"apiKey": api_key, "secret": api_secret, "password": password, "enableRateLimit": True})
            if use_sandbox:
                ex.urls['api'] = {
                    'public': 'https://openapi-sandbox.kucoin.com',
                    'private': 'https://openapi-sandbox.kucoin.com'
                }
        else:
            return False, "unsupported platform"
        await to_thread(ex.fetch_balance)
        return True, "OK"
    except Exception as e:
        return False, str(e)

async def fetch_ticker(symbol="BTC/USDT"):
    try:
        ex = ccxt.binance()
        t = await to_thread(ex.fetch_ticker, symbol)
        return t
    except Exception as e:
        return {"ask": None, "bid": None, "last": None, "info": str(e)}

async def simulate_virtual_trade(amount, symbol="BTC/USDT", bot_fee_percent=None):
    if bot_fee_percent is None:
        bot_fee_percent = float(database.get_setting("bot_fee_percent", "10"))
    ticker = await fetch_ticker(symbol)
    buy_price = ticker.get("ask") or ticker.get("last") or 0.0
    if not buy_price or buy_price == 0:
        buy_price = 30000.0
    profit_pct = random.uniform(0.005, 0.02)
    sell_price = buy_price * (1 + profit_pct)
    qty = amount / buy_price
    gross_profit = qty * (sell_price - buy_price)
    net_profit = gross_profit * (1 - bot_fee_percent/100)
    timeframe = random.choice(["1 ساعة", "6 ساعات", "24 ساعة", "3 أيام"])
    return {
        "symbol": symbol,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "qty": qty,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "timeframe": timeframe,
        "profit_pct": profit_pct * 100
    }

async def execute_real_trade(platform_entry, amount_usd, symbol="BTC/USDT", sandbox_override=None):
    """
    platform_entry: dict row from DB (platform_name, api_key, api_secret, password, api_key_test, api_secret_test, is_sandbox)
    amount_usd: مبلغ بالـ quote currency (مثلاً USDT)
    """
    platform_name = platform_entry["platform_name"].lower()
    use_sandbox = sandbox_override if sandbox_override is not None else (platform_entry.get("is_sandbox") or SANDBOX_MODE)
    # choose keys (test keys if sandbox)
    if use_sandbox and platform_entry.get("api_key_test"):
        api_key = platform_entry.get("api_key_test")
        api_secret = platform_entry.get("api_secret_test")
    else:
        api_key = platform_entry.get("api_key")
        api_secret = platform_entry.get("api_secret")
    password = platform_entry.get("password")

    # prepare exchange instance
    def make_exchange():
        if platform_name == "binance":
            ex = ccxt.binance({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
            if use_sandbox:
                ex.urls['api'] = ex.urls.get('test') or {
                    'public': 'https://testnet.binance.vision/api/v3',
                    'private': 'https://testnet.binance.vision/api/v3'
                }
            return ex
        if platform_name == "kucoin":
            ex = ccxt.kucoin({"apiKey": api_key, "secret": api_secret, "password": password, "enableRateLimit": True})
            if use_sandbox:
                ex.urls['api'] = {
                    'public': 'https://openapi-sandbox.kucoin.com',
                    'private': 'https://openapi-sandbox.kucoin.com'
                }
            return ex
        raise ValueError("Unsupported platform")

    try:
        ex = make_exchange()
        await to_thread(ex.load_markets)
        market = ex.markets.get(symbol)
        if not market:
            return {"ok": False, "msg": f"Symbol {symbol} not available on {platform_name}"}
        ticker = await to_thread(ex.fetch_ticker, symbol)
        price = ticker.get("ask") or ticker.get("last") or ticker.get("bid")
        if not price or price == 0:
            return {"ok": False, "msg": "Could not fetch market price."}
    except Exception as e:
        return {"ok": False, "msg": f"Market fetch error: {e}"}

    # compute qty and rounding
    qty = amount_usd / price
    try:
        qty_rounded = float(ex.amount_to_precision(symbol, qty)) if hasattr(ex, 'amount_to_precision') else round(qty, market['precision']['amount'])
        price_rounded = float(ex.price_to_precision(symbol, price)) if hasattr(ex, 'price_to_precision') else round(price, market['precision']['price'])
        if qty_rounded <= 0:
            return {"ok": False, "msg": "Quantity after precision is zero; amount too small."}
    except Exception:
        qty_rounded = max(0.0, round(qty, market.get('precision', {}).get('amount', 8)))
        price_rounded = round(price, market.get('precision', {}).get('price', 8))
        if qty_rounded <= 0:
            return {"ok": False, "msg": "Quantity after rounding is zero."}

    bot_fee = float(database.get_setting("bot_fee_percent", BOT_FEE_PERCENT))
    # if ALLOW_REAL_TRADES is false -> simulate but with precise rounding
    if not ALLOW_REAL_TRADES:
        profit_pct = random.uniform(0.005, 0.015)
        sell_price = price_rounded * (1 + profit_pct)
        gross_profit = qty_rounded * (sell_price - price_rounded)
        net_profit = gross_profit * (1 - bot_fee/100)
        return {
            "ok": True,
            "simulated": True,
            "platform": platform_entry["platform_name"],
            "symbol": symbol,
            "buy_price": price_rounded,
            "sell_price": sell_price,
            "qty": qty_rounded,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "note": "Simulation (ALLOW_REAL_TRADES=false)"
        }

    # execute real market buy and (optionally) market sell
    try:
        order_buy = await to_thread(ex.create_market_buy_order, symbol, qty_rounded)
        # After buy, fetch new ticker for sell estimate
        ticker_after = await to_thread(ex.fetch_ticker, symbol)
        sell_price_est = ticker_after.get("bid") or ticker_after.get("last") or price_rounded
        # In production you would create a sell order or plan TP/SL
        sell_price = sell_price_est * 1.001  # tiny margin for example
        gross_profit = qty_rounded * (sell_price - price_rounded)
        net_profit = gross_profit * (1 - bot_fee/100)
        return {
            "ok": True,
            "simulated": False,
            "platform": platform_entry["platform_name"],
            "symbol": symbol,
            "buy_order": order_buy,
            "buy_price": price_rounded,
            "sell_price": sell_price,
            "qty": qty_rounded,
            "gross_profit": gross_profit,
            "net_profit": net_profit
        }
    except Exception as e:
        return {"ok": False, "msg": f"Execution error: {e}"}
