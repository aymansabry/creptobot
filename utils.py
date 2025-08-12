import ccxt
import os
from decimal import Decimal, ROUND_DOWN
import database

# قراءة إعدادات من قاعدة البيانات
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))  # نسبة العمولة
USE_SANDBOX = database.get_setting("use_sandbox", "false").lower() == "true"  # تفعيل وضع الاختبار

# إنشاء كائن منصة
def get_exchange(name, api_key, api_secret, passphrase=None):
    name = name.lower()
    if name == "binance":
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret
        })
    elif name == "kucoin":
        exchange = ccxt.kucoin({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase
        })
    else:
        raise ValueError(f"المنصة {name} غير مدعومة حالياً")

    if USE_SANDBOX and hasattr(exchange, 'set_sandbox_mode'):
        exchange.set_sandbox_mode(True)

    exchange.load_markets()
    return exchange


# دالة لضبط الكمية والسعر حسب دقة السوق
def adjust_amount(exchange, symbol, amount):
    market = exchange.market(symbol)
    precision = market['precision']['amount']
    return float(Decimal(amount).quantize(Decimal(str(10 ** -precision)), rounding=ROUND_DOWN))


def adjust_price(exchange, symbol, price):
    market = exchange.market(symbol)
    precision = market['precision']['price']
    return float(Decimal(price).quantize(Decimal(str(10 ** -precision)), rounding=ROUND_DOWN))


# تنفيذ أمر سوق (Market Order)
def execute_market_order(exchange, symbol, side, amount):
    amount = adjust_amount(exchange, symbol, amount)
    print(f"🚀 تنفيذ أمر سوق {side} على {symbol} بكمية {amount}")
    try:
        order = exchange.create_market_order(symbol, side, amount)
        return order
    except Exception as e:
        print(f"❌ خطأ أثناء تنفيذ الأمر: {e}")
        return None


# حساب الربح بعد خصم العمولة
def calculate_profit(entry_price, exit_price, amount):
    gross_profit = (exit_price - entry_price) * amount
    net_profit = gross_profit - (gross_profit * BOT_FEE_PERCENT / 100)
    return round(net_profit, 8)


# وضع اختبار الصفقة
def simulate_trade(entry_price, exit_price, amount):
    profit = calculate_profit(entry_price, exit_price, amount)
    return {
        "entry_price": entry_price,
        "exit_price": exit_price,
        "amount": amount,
        "profit": profit
    }
