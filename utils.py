# utils.py
import ccxt
import math
from database import get_setting  # دالة لاستدعاء إعداد من جدول settings

SANDBOX_MODE = True  # يمكن التحكم فيها ديناميكياً لو حبينا من قاعدة البيانات

def validate_api_keys(platform, api_key, api_secret):
    try:
        exchange = get_exchange(platform, api_key, api_secret, test_connection=True)
        # تحقق بسيط بجلب الرصيد أو الأسواق حسب المنصة
        if platform in ['binance', 'kucoin']:
            exchange.fetch_balance()
        else:
            return False
        return True
    except Exception:
        return False

def get_exchange(platform, api_key=None, api_secret=None, test_connection=False):
    exchange_class = getattr(ccxt, platform)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

    if SANDBOX_MODE:
        if platform == 'binance':
            exchange.set_sandbox_mode(True)
        elif platform == 'kucoin':
            exchange.urls['api'] = exchange.urls['test']
            exchange.headers = {'x-sandbox': 'true'}

    if test_connection:
        exchange.load_markets()

    return exchange

def place_market_order(exchange, symbol, side, amount):
    markets = exchange.load_markets()
    market = markets[symbol]
    precision = market['precision']['amount']

    amount_rounded = round_down(amount, precision)
    order = exchange.create_order(symbol, 'market', side, amount_rounded)
    return order

def round_down(number, decimals=0):
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    factor = 10 ** decimals
    return math.floor(number * factor) / factor

def calculate_profit(gross_profit):
    try:
        fee_percent_str = get_setting("bot_fee_percent", "10")  # افتراض 10%
        fee_percent = float(fee_percent_str) / 100
    except Exception:
        fee_percent = 0.10  # قيمة افتراضية

    fee = gross_profit * fee_percent
    net_profit = gross_profit - fee
    return round(net_profit, 8), round(fee, 8)
