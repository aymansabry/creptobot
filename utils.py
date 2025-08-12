import ccxt
import decimal
from database import get_setting

# قراءة الإعدادات العامة من قاعدة البيانات
BOT_FEE_PERCENT = float(get_setting("bot_fee_percent", "10"))
USE_SANDBOX = get_setting("use_sandbox", "true").lower() == "true"

# دالة ضبط الرقم حسب دقة السوق
def adjust_amount(exchange, symbol, amount):
    try:
        markets = exchange.load_markets()
        precision = markets[symbol]['precision']['amount']
        return float(round(decimal.Decimal(amount), precision))
    except Exception as e:
        print(f"⚠️ خطأ في adjust_amount: {e}")
        return amount

# إنشاء اتصال مع المنصة
def create_exchange(name, api_key, api_secret, sandbox=False):
    name = name.lower()
    if name == "binance":
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
    elif name == "kucoin":
        exchange = ccxt.kucoin({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
    else:
        raise ValueError(f"منصة غير مدعومة: {name}")

    if sandbox:
        if name == "binance":
            exchange.set_sandbox_mode(True)
        elif name == "kucoin":
            exchange.urls['api'] = exchange.urls['test']
    return exchange

# تنفيذ أمر سوق
def place_market_order(exchange, symbol, side, amount):
    try:
        amount = adjust_amount(exchange, symbol, amount)
        order = exchange.create_market_order(symbol, side, amount)
        print(f"✅ تم تنفيذ أمر سوق: {order}")
        return order
    except Exception as e:
        print(f"❌ فشل تنفيذ أمر السوق: {e}")
        return None

# تنفيذ أمر سوق وهمي للتجربة
def place_sandbox_market_order(exchange, symbol, side, amount):
    try:
        print(f"[SANDBOX] تنفيذ أمر سوق وهمي {side} {amount} {symbol}")
        return {"symbol": symbol, "side": side, "amount": amount, "status": "sandbox_executed"}
    except Exception as e:
        print(f"❌ خطأ في sandbox: {e}")
        return None
