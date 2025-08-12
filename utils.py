# utils.py
import ccxt
import database
from decimal import Decimal, ROUND_DOWN

# إعداد نسبة رسوم البوت من الإعدادات أو 10% افتراضي
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

# إنشاء كائن المنصة
def get_exchange_client(user_id):
    ex_data = database.get_exchange(user_id)
    if not ex_data:
        raise ValueError("❌ لا يوجد بيانات منصة للمستخدم")

    exchange_class = getattr(ccxt, ex_data["exchange_name"])
    params = {
        "apiKey": ex_data["api_key"],
        "secret": ex_data["api_secret"]
    }

    if ex_data["sandbox"]:
        params["enableRateLimit"] = True
        client = exchange_class(params)
        client.set_sandbox_mode(True)
    else:
        client = exchange_class(params)

    return client

# ضبط الكمية حسب دقة المنصة
def adjust_amount(amount, precision):
    amount = Decimal(str(amount))
    precision = Decimal(str(precision))
    return float(amount.quantize(precision, rounding=ROUND_DOWN))

# تنفيذ أمر سوق
def place_market_order(user_id, symbol, side, amount):
    client = get_exchange_client(user_id)
    markets = client.load_markets()

    if symbol not in markets:
        raise ValueError(f"❌ الزوج {symbol} غير موجود في المنصة")

    market = markets[symbol]
    precision = market.get("precision", {}).get("amount", 6)
    rounded_amount = adjust_amount(amount, Decimal("1e-{0}".format(precision)))

    order = client.create_market_order(symbol, side, rounded_amount)
    return order

# تنفيذ عملية استثمار
def execute_investment(user_id, symbol, amount_usd):
    client = get_exchange_client(user_id)
    ticker = client.fetch_ticker(symbol)
    price = ticker["last"]

    amount = amount_usd / price
    order = place_market_order(user_id, symbol, "buy", amount)

    # حساب رسوم البوت
    fee = amount_usd * BOT_FEE_PERCENT / 100
    print(f"✅ تم تنفيذ الصفقة: شراء {amount} من {symbol} بسعر {price}، رسوم البوت {fee} USD")

    return order

# تنفيذ بيع
def execute_sell(user_id, symbol, amount):
    order = place_market_order(user_id, symbol, "sell", amount)
    print(f"✅ تم بيع {amount} من {symbol}")
    return order

# وضع اختبار Sandbox
def test_sandbox_order(user_id, symbol, side, amount):
    ex_data = database.get_exchange(user_id)
    if not ex_data:
        raise ValueError("❌ لا يوجد بيانات منصة للمستخدم")

    # نجبر على التشغيل في وضع sandbox
    database.save_exchange(
        ex_data["user_id"],
        ex_data["exchange_name"],
        ex_data["api_key"],
        ex_data["api_secret"],
        sandbox=True
    )

    return place_market_order(user_id, symbol, side, amount)
