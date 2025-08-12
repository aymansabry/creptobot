# utils.py
import ccxt
import database
import decimal

# وضع التنفيذ (True = فعلي, False = وهمي)
REAL_TRADING = True

def get_exchange(name, api_key=None, api_secret=None, sandbox=False):
    """
    إنشاء اتصال بالمنصة مع إمكانية تفعيل وضع التجربة (Sandbox).
    """
    exchange_class = getattr(ccxt, name.lower())()
    if api_key and api_secret:
        exchange_class.apiKey = api_key
        exchange_class.secret = api_secret

    if sandbox and hasattr(exchange_class, 'set_sandbox_mode'):
        exchange_class.set_sandbox_mode(True)

    return exchange_class

def adjust_amount(exchange, symbol, amount):
    """
    ضبط كمية الطلب بناءً على precision المنصة.
    """
    markets = exchange.load_markets()
    market = markets.get(symbol, None)
    if not market:
        raise ValueError(f"⚠️ الزوج {symbol} غير مدعوم على {exchange.id}")

    precision = market['precision']['amount']
    return float(round(decimal.Decimal(amount), precision))

def place_market_order(exchange, symbol, side, amount):
    """
    تنفيذ أمر سوق (Market Order) مع مراعاة الـ precision.
    """
    try:
        adj_amount = adjust_amount(exchange, symbol, amount)
        order = exchange.create_order(symbol, "market", side, adj_amount)
        return order
    except Exception as e:
        return {"error": str(e)}

def execute_trade(exchange_name, symbol, side, amount, user_id):
    """
    تنفيذ الصفقة (فعلي أو وهمي) بناءً على وضع التداول.
    """
    api_key, api_secret = database.get_api_keys_for_exchange(exchange_name, user_id)
    exchange = get_exchange(exchange_name, api_key, api_secret, sandbox=not REAL_TRADING)

    if not REAL_TRADING:
        return {"status": "sandbox", "message": f"تمت محاكاة {side} {amount} من {symbol} على {exchange_name}"}

    return place_market_order(exchange, symbol, side, amount)

