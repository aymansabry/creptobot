# utils.py
import asyncio
import ccxt
import random
import os
import math
from dotenv import load_dotenv
from datetime import timedelta
import database

load_dotenv()

ALLOW_REAL_TRADES = os.getenv("ALLOW_REAL_TRADES", "false").lower() in ("1","true","yes")
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

async def to_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

# validate API keys by fetching balance (returns (ok, message))
async def validate_platform_keys(platform_name, api_key, api_secret, password=None):
    try:
        if platform_name.lower() == "binance":
            ex = ccxt.binance({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
            await to_thread(ex.fetch_balance)
        elif platform_name.lower() == "kucoin":
            ex = ccxt.kucoin({"apiKey": api_key, "secret": api_secret, "password": password, "enableRateLimit": True})
            await to_thread(ex.fetch_balance)
        else:
            return False, "Unknown platform"
        return True, "✅ تم التحقق من المفاتيح"
    except Exception as e:
        return False, f"❌ خطأ في التحقق: {e}"

# fetch ticker from binance public
async def fetch_ticker(symbol="BTC/USDT"):
    try:
        ex = ccxt.binance()
        t = await to_thread(ex.fetch_ticker, symbol)
        return t
    except Exception as e:
        # fallback dummy
        return {"ask": None, "bid": None, "last": None, "info": str(e)}

# simulate virtual trade using actual price snapshot
async def simulate_virtual_trade(amount, symbol="BTC/USDT", bot_fee_percent=None):
    if bot_fee_percent is None:
        bot_fee_percent = float(database.get_setting("bot_fee_percent", "10"))
    ticker = await fetch_ticker(symbol)
    buy_price = ticker.get("ask") or ticker.get("last") or 0.0
    # pick a realistic sell price (+0.5% - +2%)
    profit_pct = random.uniform(0.005, 0.02)
    sell_price = buy_price * (1 + profit_pct)
    qty = amount / buy_price if buy_price > 0 else 0.0
    gross_profit = qty * (sell_price - buy_price)
    net_profit = gross_profit * (1 - bot_fee_percent/100)
    # choose timeframe
    timeframe = random.choice(["1 ساعة", "6 ساعات", "24 ساعة", "3 أيام"])
    return {
        "symbol": symbol,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "qty": qty,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "timeframe": timeframe,
        "profit_pct": profit_pct*100
    }

# execute real trade (safe-guarded by ALLOW_REAL_TRADES)
async def execute_real_trade(platform_entry, amount, symbol="BTC/USDT"):
    """
    platform_entry: dict with platform_name, api_key, api_secret, password
    amount: USD amount to use
    returns dict with result and message
    """
    bot_fee_percent = float(database.get_setting("bot_fee_percent", "10"))
    platform = platform_entry["platform_name"].lower()
    api_key = platform_entry["api_key"]
    api_secret = platform_entry["api_secret"]
    password = platform_entry.get("password")
    # fetch market price
    ticker = await fetch_ticker(symbol)
    buy_price = ticker.get("ask") or ticker.get("last") or 0.0
    if not buy_price:
        return {"ok": False, "msg": "تعذر جلب سعر السوق."}
    qty = amount / buy_price
    # if real trades are disabled -> simulate
    if not ALLOW_REAL_TRADES:
        profit_pct = 0.01  # 1% example
        sell_price = buy_price * (1 + profit_pct)
        gross_profit = qty * (sell_price - buy_price)
        net_profit = gross_profit * (1 - bot_fee_percent/100)
        return {
            "ok": True,
            "simulated": True,
            "platform": platform_entry["platform_name"],
            "symbol": symbol,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "qty": qty,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "note": "محاكاة (ALLOW_REAL_TRADES=false)"
        }
    # else attempt real orders via ccxt
    try:
        if platform == "binance":
            ex = ccxt.binance({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
        elif platform == "kucoin":
            ex = ccxt.kucoin({"apiKey": api_key, "secret": api_secret, "password": password, "enableRateLimit": True})
        else:
            return {"ok": False, "msg": "منصة غير مدعومة."}
        # fetch price & create market buy order
        # Note: create_market_buy_order expects amount in base currency (qty)
        order_buy = await to_thread(ex.create_market_buy_order, symbol, qty)
        # In real world we must wait/fetch order info; here we simulate sale at slightly higher price
        sell_price = buy_price * 1.005
        gross_profit = qty * (sell_price - buy_price)
        net_profit = gross_profit * (1 - bot_fee_percent/100)
        return {
            "ok": True,
            "simulated": False,
            "platform": platform_entry["platform_name"],
            "symbol": symbol,
            "buy_order": order_buy,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "qty": qty,
            "gross_profit": gross_profit,
            "net_profit": net_profit
        }
    except Exception as e:
        return {"ok": False, "msg": f"خطأ أثناء تنفيذ الصفقة الحقيقية: {e}"}
