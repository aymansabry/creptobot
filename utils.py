# utils.py
import ccxt
import database
import random
import time

# جلب إعدادات عامة
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))  # نسبة العمولة
SANDBOX_MODE = database.get_setting("sandbox_mode", "false").lower() == "true"

# ==========================
# إنشاء اتصال بالمنصة
# ==========================
def get_exchange(platform, api_key=None, api_secret=None):
    exchanges = {
        "binance": ccxt.binance,
        "kucoin": ccxt.kucoin,
        "bybit": ccxt.bybit
    }
    if platform not in exchanges:
        raise ValueError(f"المنصة {platform} غير مدعومة.")

    exchange_class = exchanges[platform]
    exchange = exchange_class({
        "apiKey": api_key,
        "secret": api_secret
    })

    # تفعيل وضع الاختبار إذا كان مفعّل
    if SANDBOX_MODE:
        if hasattr(exchange, "set_sandbox_mode"):
            exchange.set_sandbox_mode(True)

    return exchange

# ==========================
# الحصول على دقة التداول
# ==========================
def get_market_precision(exchange, symbol):
    markets = exchange.load_markets()
    market = markets.get(symbol)
    if not market:
        raise ValueError(f"زوج {symbol} غير موجود على {exchange.id}")
    amount_precision = market.get("precision", {}).get("amount", 8)
    price_precision = market.get("precision", {}).get("price", 8)
    return amount_precision, price_precision

# ==========================
# تنفيذ أمر سوق (Market Order)
# ==========================
def place_market_order(exchange, symbol, side, amount):
    amount_precision, _ = get_market_precision(exchange, symbol)
    amount = round(amount, amount_precision)

    print(f"🔹 تنفيذ أمر سوق {side} على {symbol} بالكمية {amount} في {exchange.id}")
    try:
        order = exchange.create_order(symbol, "market", side, amount)
        return order
    except Exception as e:
        print(f"❌ فشل تنفيذ الأمر: {e}")
        return None

# ==========================
# تنفيذ صفقة (حقيقية أو وهمية)
# ==========================
def execute_trade(telegram_id, platform, symbol, side, amount):
    user = database.get_user_by_telegram_id(telegram_id)
    if not user:
        raise ValueError("المستخدم غير موجود.")

    # جلب مفاتيح API
    conn = database.get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT api_key, api_secret FROM api_keys WHERE user_id=%s AND platform=%s", (user["id"], platform))
    api_data = cur.fetchone()
    cur.close()
    conn.close()

    if not api_data:
        raise ValueError("لم يتم ضبط مفاتيح API الخاصة بك.")

    exchange = get_exchange(platform, api_data["api_key"], api_data["api_secret"])

    if SANDBOX_MODE:
        # تنفيذ وهمي
        fake_price = random.uniform(100, 500)
        total = amount * fake_price
        print(f"💡 تنفيذ وهمي {side} {amount} {symbol} بسعر {fake_price} - إجمالي {total}")
        return {
            "type": "sandbox",
            "side": side,
            "amount": amount,
            "price": fake_price,
            "total": total
        }
    else:
        # تنفيذ حقيقي
        return place_market_order(exchange, symbol, side, amount)
