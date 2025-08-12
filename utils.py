# utils.py
import ccxt
import logging
from decimal import Decimal, ROUND_DOWN
from config import SANDBOX_MODE
import database

# قراءة نسبة عمولة البوت من قاعدة البيانات
BOT_FEE_PERCENT = float(database.get_setting("bot_fee_percent", "10"))

# إعداد اللوج
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دالة تجهيز الاتصال بالمنصة
def get_exchange(exchange_name, api_key, api_secret):
    try:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret
        })
        if SANDBOX_MODE and hasattr(exchange, 'set_sandbox_mode'):
            exchange.set_sandbox_mode(True)
        return exchange
    except AttributeError:
        raise ValueError(f"Exchange '{exchange_name}' not supported.")

# دالة لضبط الكمية حسب precision المنصة
def adjust_amount(exchange, symbol, amount):
    markets = exchange.load_markets()
    market = markets.get(symbol)
    if not market:
        raise ValueError(f"Market {symbol} not found on {exchange.id}")
    precision = market['precision']['amount']
    return float(Decimal(amount).quantize(Decimal(10) ** -precision, rounding=ROUND_DOWN))

# دالة لتنفيذ أمر Market
def place_market_order(exchange, symbol, side, amount):
    amount = adjust_amount(exchange, symbol, amount)
    logger.info(f"Placing {side} market order: {symbol}, amount={amount}")
    if SANDBOX_MODE:
        logger.info("[SANDBOX] Order not executed on real market.")
        return {"sandbox": True, "symbol": symbol, "side": side, "amount": amount}
    return exchange.create_market_order(symbol, side, amount)

# حساب الربح بعد عمولة البوت
def calculate_profit(total_profit):
    fee = (BOT_FEE_PERCENT / 100) * total_profit
    net_profit = total_profit - fee
    return round(net_profit, 8), round(fee, 8)

# التحقق من API Keys
def validate_api_keys(exchange_name, api_key, api_secret):
    try:
        exchange = get_exchange(exchange_name, api_key, api_secret)
        exchange.fetch_balance()
        return True
    except Exception as e:
        logger.error(f"API Key validation failed for {exchange_name}: {str(e)}")
        return False
