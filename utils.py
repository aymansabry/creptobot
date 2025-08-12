# utils.py
import ccxt
import decimal
from database import get_setting, set_setting, get_connection
from datetime import datetime

# إعدادات عامة
BOT_FEE_PERCENT = float(get_setting("bot_fee_percent", 10))
USE_SANDBOX = get_setting("use_sandbox", "false").lower() == "true"

# ====== سجلات ======
def log_message(message):
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO logs (message) VALUES (%s)", (message,))
        conn.commit()
        cur.close()
        conn.close()

# ====== إعداد منصة التداول ======
def get_exchange(name, api_key, api_secret):
    exchange_class = getattr(ccxt, name)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': api_secret
    })
    if USE_SANDBOX and hasattr(exchange, 'set_sandbox_mode'):
        exchange.set_sandbox_mode(True)
    return exchange

# ====== جلب دقة السعر والحجم ======
def get_symbol_precision(exchange, symbol):
    markets = exchange.load_markets()
    market = markets.get(symbol)
    if not market:
        raise ValueError(f"Symbol {symbol} not found on {exchange.id}")
    price_precision = market['precision'].get('price', 8)
    amount_precision = market['precision'].get('amount', 8)
    return price_precision, amount_precision

# ====== تنفيذ أمر سوق ======
def execute_market_order(exchange, symbol, side, amount):
    price_precision, amount_precision = get_symbol_precision(exchange, symbol)
    amount = float(decimal.Decimal(amount).quantize(decimal.Decimal(f"1e-{amount_precision}")))
    
    order = exchange.create_market_order(symbol, side, amount)
    log_message(f"Market Order: {symbol} {side} {amount} - {order}")
    return order

# ====== حساب الربح بعد العمولة ======
def calculate_profit_with_fee(profit):
    fee = (BOT_FEE_PERCENT / 100) * profit
    net_profit = profit - fee
    return net_profit

# ====== إضافة صفقة للتاريخ ======
def save_trade(user_id, exchange_name, symbol, side, price, amount, profit_loss):
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO trades (user_id, exchange_name, symbol, side, price, amount, profit_loss)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, exchange_name, symbol, side, price, amount, profit_loss))
        conn.commit()
        cur.close()
        conn.close()
