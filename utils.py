# utils.py
import os
import ccxt
import math
from decimal import Decimal, ROUND_DOWN
from database import SessionLocal, get_setting
from contextlib import contextmanager

# مدير جلسة قاعدة البيانات (للاستخدام السهل)
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# جلب نسبة ربح البوت من قاعدة البيانات (كنسبة عشرية)
def get_bot_fee_percent():
    with get_db_session() as db:
        fee_str = get_setting(db, "bot_fee_percent", "10")
    try:
        return float(fee_str)
    except:
        return 10.0  # القيمة الافتراضية

# ضبط دقة الأسعار حسب منصة
EXCHANGE_PRECISION = {
    "binance": 8,
    "kucoin": 8,
    # أضف منصات أخرى هنا حسب الحاجة
}

def round_price(exchange_name: str, price: float) -> float:
    precision = EXCHANGE_PRECISION.get(exchange_name.lower(), 8)
    factor = 10 ** precision
    return math.floor(price * factor) / factor

# إنشاء عميل ccxt للمنصة بالـ API key و secret
def create_exchange_client(exchange_name, api_key=None, api_secret=None, sandbox=False):
    exchange_cls = getattr(ccxt, exchange_name.lower(), None)
    if exchange_cls is None:
        raise ValueError(f"Exchange {exchange_name} not supported.")

    params = {}
    if sandbox:
        # مفعل وضع sandbox إذا توفر لدى المنصة (binance مثلا)
        if exchange_name.lower() == "binance":
            params['options'] = {'defaultType': 'future'}
            params['urls'] = {'api': {'public': 'https://testnet.binance.vision/api',
                                     'private': 'https://testnet.binance.vision/api'}}
        elif exchange_name.lower() == "kucoin":
            params['urls'] = {'api': 'https://openapi-sandbox.kucoin.com'}
        # أضف أي منصات تدعم sandbox هنا

    exchange = exchange_cls({
        'apiKey': api_key,
        'secret': api_secret,
        **params,
        'enableRateLimit': True,
    })

    return exchange

# جلب سعر السوق الحالي لعملة معينة
def fetch_current_price(exchange_name, symbol):
    try:
        exchange = create_exchange_client(exchange_name)
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"Error fetching price from {exchange_name} for {symbol}: {e}")
        return None

# حساب الربح بعد خصم نسبة البوت
def calculate_profit(gross_profit: float) -> float:
    fee_percent = get_bot_fee_percent()
    net_profit = gross_profit * (1 - fee_percent / 100)
    return net_profit

# تنفيذ صفقة سوق (شراء/بيع) مع rounding للسعر
def execute_market_order(exchange_name, api_key, api_secret, symbol, side, amount, sandbox=False):
    exchange = create_exchange_client(exchange_name, api_key, api_secret, sandbox)
    try:
        # هنا فقط مثال لطلب سعر السوق وتنفيذ السوق مباشرة
        # لاحظ: بعض المنصات لا تدعم السوق مباشرة ويحتاجون أوامر ليمت أو طريقة أخرى
        # إذا المنصة تدعم السوق مباشرة:
        order = exchange.create_order(symbol, 'market', side, amount)
        return order
    except Exception as e:
        print(f"Order execution error on {exchange_name}: {e}")
        return None
